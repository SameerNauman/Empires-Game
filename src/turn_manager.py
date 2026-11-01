import pygame
from enemy_ai import EnemyAi
from config import *

class TurnManager:
    def __init__(self):
        self.enemy_ai = EnemyAi()
        # Turn tracking variables
        self.enemy_turn_index = 0
        self.enemy_turn_phase = 'move'
        self.enemy_turn_delay = 0
        self.enemy_paths_planned = False

    # Player turn begins, processes transition fade.
    def end_enemy_day(self, game_state):
        game_state.player_turn = True 
        
        game_state.fade_manager.start_fade()
        game_state.day_processed_mid_fade = False

    # Activates tech researched from buildings.
    def complete_research(self, tech_key, game_state, side='player'): 
        if side == 'player':
            target_researched = game_state.researched_techs
            multipliers = game_state.tech_multipliers # Player stats
        else:
            target_researched = game_state.enemy_researched_techs
            # Ensure you have initialized self.enemy_tech_multipliers in __init__
            multipliers = game_state.enemy_tech_multipliers 
        
        if tech_key not in target_researched:
            target_researched.add(tech_key)
            
            effect_key = RESEARCH[tech_key][5]
            effect_val = RESEARCH[tech_key][6]
            
            if "rate" in effect_key:
                multipliers[effect_key] *= effect_val
            else:
                multipliers[effect_key] += effect_val

            if side == 'player' and "vision" in effect_key:
                game_state.update_VISIBILITY_MAP()

    # Processes player's resource gathering at the end of enemy turn
    def process_automatic_gathering(self, game_state):
        # Iterates over all units and checks if they are gathering. 
        for unit in game_state.units:
            if unit.is_gathering:
                res_id = unit.gather_resource_id
                res = next((r for r in game_state.resources if r.id == res_id), None)
                unit_tile = (int(unit.x), int(unit.y))
                
                if res and (res.x, res.y) == unit_tile:
                    # Determine base amount to take from the resource tile
                    raw_amount = min(100, res.amount)
                    res.amount -= raw_amount
                    
                    # Apply the specific multiplier based on resource type
                    if res.resource_type == "food":
                        multiplier = game_state.tech_multipliers.get("gather_rate_food", 1.0)
                        game_state.food_amount += int(raw_amount * multiplier)
                        
                    elif res.resource_type == "wood":
                        multiplier = game_state.tech_multipliers.get("gather_rate_wood", 1.0)
                        game_state.wood_amount += int(raw_amount * multiplier)
                        
                    elif res.resource_type == "gold":
                        multiplier = game_state.tech_multipliers.get("gather_rate_gold", 1.0)
                        game_state.gold_amount += int(raw_amount * multiplier)

                    # Handle depletion
                    if res.amount <= 0:
                        game_state.resources.remove(res)
                        game_state.message_box.open(f"{res.resource_type} has been depleted.", game_state.error_message)
                        unit.is_gathering = False
                        unit.gather_resource_id = None

    # Processed enemy's resource gathering at the end of enemy turn
    def process_enemy_gathering(self, game_state):
        # Iterates over all enemy units and checks if they are gathering. 
        for unit in game_state.enemy_units:
            if unit.is_gathering:
                res_id = unit.gather_resource_id
                # Iterates over resources and checks if their ID matches the one the unit is gathering
                # from. If the unit is gathering from a resource tile its on, it processes the gathering,
                # and if the resource has been depleted, it is deleted.
                res = next((r for r in game_state.resources if r.id == res_id), None)
                unit_tile = (int(unit.x), int(unit.y))
                if res and (res.x, res.y) == unit_tile:
                    amount_gathered = min(100, res.amount)
                    res.amount -= amount_gathered
                    if res.resource_type == "food":
                        game_state.enemy_food += amount_gathered
                    elif res.resource_type == "wood":
                        game_state.enemy_wood += amount_gathered
                    elif res.resource_type == "gold":
                        game_state.enemy_gold += amount_gathered
                    if res.amount <= 0:
                        game_state.resources.remove(res)
                        game_state.message_box.open(f"{res.resource_type} has been depleted.", True)
                        unit.is_gathering = False
                        unit.gather_resource_id = None
                
                print("food:", game_state.enemy_food, "wood:", game_state.enemy_wood, "gold:", game_state.enemy_gold)

    # def process_enemy_construction(self, game_state):
    #         completed_villagers = []
    
    #         for villager, building in game_state.enemy_construction_tasks.items():
    #             # Check if the villager is still alive and at the correct location
    #             if villager.health > 0 and int(villager.x) == int(building.x) and int(villager.y) == int(building.y):
    #                 building.is_constructed = True
    #                 building.rested() # Reset action counts for the new building
    #                 completed_villagers.append(villager)
    #                 print(f"AI finished building: {building.type}")
    #             else:
    #                 # If the villager walked away or died, stop the task
    #                 completed_villagers.append(villager)
    
    #         # Clean up the dictionary so villagers can take new jobs
    #         for v in completed_villagers:
    #             del game_state.enemy_construction_tasks[v]
    
    def process_entity_health(self, game_state):
        # Player units
        for unit in game_state.units:
            if unit.health <= 0:
                print(f"Player at ({unit.x},{unit.y}) is defeated!")
                # Remove any dead units from construction dictionary.
                for key in list(game_state.construction):
                    if key == unit:
                        game_state.construction.pop(key)
                game_state.units.remove(unit)

        # Player buildings
        for building in game_state.buildings:
            if building.hitpoints <= 0:
                print(f"Building at ({building.x},{building.y}) is destroyed!")
                game_state.buildings.remove(building)

        # Enemy units
        for enemy in game_state.enemy_units:
            if enemy.health <= 0:
                game_state.enemy_units.remove(enemy)
                print(enemy, "died")

        # Enemy buildings
        for eb in game_state.e_buildings:
            if eb.hitpoints <= 0:
                print(f"Building at ({eb.x},{eb.y}) is destroyed!")
                game_state.e_buildings.remove(eb)
        
    # Updates the enemy unit paths.
    def update_enemy_turn(self, game_state):
        if not self.enemy_paths_planned:
            self.enemy_ai.execute_turn(
                game_state.enemy_units, 
                game_state.units, 
                game_state.buildings, 
                game_state.resources, 
                game_state.e_buildings, 
                game_state
            )
            self.enemy_paths_planned = True
            self.enemy_turn_index = 0
            self.enemy_turn_phase = 'move'
            self.enemy_turn_delay = 0

        # If all enemies processed, the enemy turn ends
        if self.enemy_turn_index >= len(game_state.enemy_units):
            self.end_enemy_day(game_state)
            return

        enemy = game_state.enemy_units[self.enemy_turn_index]
        # Delay between actions for clarity/animation (e.g. 15 frames = 0.25s at 60 FPS)
        if self.enemy_turn_delay > 0:
            self.enemy_turn_delay -= 1
            return

        if self.enemy_turn_phase == 'move':
            # Animate movement
            if enemy.path:
                enemy.move_along_path()
                game_state.follow_enemy_camera(enemy)
                # Only move one tile per frame or step (for clarity/animation)
                self.enemy_turn_delay = 0  # Adjust as needed for game speed
                if not enemy.path:
                    self.enemy_turn_phase = 'attack'
            else:
                self.enemy_turn_phase = 'attack'

        elif self.enemy_turn_phase == 'attack':
            # Try to attack player unit/building
            did_attack = False
            attack_range = getattr(enemy, "attack_range", 1)

            # Identify potential targets
            targets = [(u, 'unit') for u in game_state.units if u.health > 0] + \
                    [(b, 'building') for b in game_state.buildings if getattr(b, 'hitpoints', 0) > 0]

            for target, target_type in targets:
                dist = abs(enemy.x - target.x) + abs(enemy.y - target.y)
                
                # Melee must be dist == 1, Ranged must be 1 < dist <= range
                is_in_range = (attack_range == 1 and dist == 1) or (attack_range > 1 and 1 < dist <= attack_range)

                if is_in_range:
                    # If target is a building, check if a player unit is standing on it (protection)
                    if target_type == 'building':
                        if any(int(u.x) == int(target.x) and int(u.y) == int(target.y) for u in game_state.units):
                            continue # Unit protects the building

                    # Calculate and apply damage
                    defense = target.defense if target_type == 'unit' else getattr(target, 'defense', 1)
                    damage = ((enemy.attack * (1 + BONUS_MULTIPLYER)) / defense) * 25 + FLAT_BONUS
                    
                    if target_type == 'unit':
                        target.health -= damage
                        game_state.retaliate_attack(enemy, target, dist) # Only units retaliate
                    else:
                        target.hitpoints -= enemy.attack # Buildings usually take raw attack or scaled damage

                    did_attack = True
                    break # One attack per turn
            self.enemy_turn_delay = 10  # Pause after attack for clarity/animation
            self.enemy_turn_index += 1
            self.enemy_turn_phase = 'move'
    
    def process_day_transition(self, game_state):
        # Completes any pending enemy techs and then clears the pending queue
        if game_state.enemy_pending_techs:
            for tech in game_state.enemy_pending_techs:
                self.complete_research(tech, game_state, side='enemy')
            game_state.enemy_pending_techs.clear()

        # Completes any pending player techs and then clears the pending queue
        if game_state.pending_techs:
            for tech in game_state.pending_techs:
                self.complete_research(tech, game_state, side='player')
            game_state.pending_techs.clear() 

        self.enemy_paths_planned = False

        # Income updates
        self.process_automatic_gathering(game_state)
        self.process_enemy_gathering(game_state)

        # Production phase
        self.enemy_ai.train_enemy_units(game_state)

        # Build queues resolution
        for building in game_state.buildings:
            if getattr(building, 'queued', False):
                building.is_constructed = True
                building.queued = False 
                building.rested()

                for key, value in list(game_state.construction.items()):
                    if value == building:
                        game_state.construction.pop(key)
        
        for building in game_state.e_buildings:
            if getattr(building, 'queued', False):
                building.is_constructed = True
                building.queued = False 

        # Check entity health
        self.process_entity_health(game_state)
        # Step time forward
        game_state.day += 1