class BasicMonster:
    def __init__(self):
        self.owner = None
    
    def take_turn(self, player, game_map, message_log):
        monster = self.owner
        
        # Only take a turn if monster is visible
        if game_map.visible[monster.y][monster.x]:
            # Check if monster is adjacent to the player
            if abs(monster.x - player.x) <= 1 and abs(monster.y - player.y) <= 1:
                # Monster is adjacent to player, attack!
                if monster.fighter:
                    attack_message = monster.fighter.attack(player, message_log)
                    if attack_message:
                        message_log.add_message(str(attack_message))
            else:
                # Basic pathfinding - move towards player
                dx = player.x - monster.x
                dy = player.y - monster.y
                distance = max(abs(dx), abs(dy))
                
                if distance > 0:
                    dx = int(round(dx / distance))
                    dy = int(round(dy / distance))
                    
                    # Don't move onto stairs
                    new_x, new_y = monster.x + dx, monster.y + dy
                    if (0 <= new_x < game_map.width and 0 <= new_y < game_map.height and
                        game_map.tiles[new_y][new_x] not in 
                        [game_map.tiles[new_y][new_x].__class__.STAIRS_UP, 
                         game_map.tiles[new_y][new_x].__class__.STAIRS_DOWN, 
                         game_map.tiles[new_y][new_x].__class__.WALL] and
                        not game_map.is_blocked(new_x, new_y)):
                        monster.move(dx, dy, game_map, message_log)
