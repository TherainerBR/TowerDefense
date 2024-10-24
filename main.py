from random import randint
import math
import time
import pygame
import sys
from settings import *


# Define a utility function to calculate the Euclidean distance between two points
def calculate_distance(pos1, pos2):
  return math.sqrt((pos1[0] - pos2[0])**2 + (pos2[1] - pos1[1]) ** 2)

# Define the main Game class
class Game:
  # Initialize the Game object
  def __init__(self, screen):
    # Store the game screen
    self.screen = screen
    
    # Create a Clock object to control the game's framerate
    self.clock = pygame.time.Clock()
    
    # Set the game's running state to True
    self.running = True
    
    # Initialize empty lists for game entities
    self.towers = []
    self.enemies = []
    self.bullets = []
    self.explosions = [] # List to keep track of explosions
    self.placing_tower = False # Flag for placing tower
    self.tower_preview_pos = None
    # Store the mouse position for the tower preview
    
    # Initialize game statistics
    self.resources = INITIAL_RESOURCES
    self.wave_number = 1
    self.enemies_spawned = 0
    self.enemies_killed = 0
    self.damage_dealt = 0
    self.start_time = time.time()
    
    # Define the enemy path as a list of cordinate tuples
    self.path = [
      (50, 50),   # Start at the top-left
      (350, 50),  # Move right
      (350, 250), # Move down to center
      (150, 250), # Move left to fill the left side
      (150, 450), # Move down
      (450, 150), # Move up
      (650, 150), # Move right towards the right side
      (650, 350), # Move down in the right side
      (300, 350), # Move left back towards the center
      (350, 550),  # Move down towards the bottom-left
      (750, 550),  # Move to bottom-right corner (exit)
    ]
    
    # Initialize the timer for enemy spawning
    self.last_enemy_spawn_time = 0
  
  def run(self):
    # Main game loop
    while self.running:
      self.clock.tick(FPS) # Limit the game to the specified frames per second
      self.handle_events() # Process game events
      self.spawn_enemies() # Spawn new enemies
      self.update_entities() # Update all enemies entities
      self.render() # Draw the game state
      self.check_game_over() # Check if the game should end
      
  def handle_enevts(self):
    # Process all pygame game events
    for event in pygame.event.get():
      if event.type == pygame.QUIT: # If the user closes the window
        self.running = False # End the game if the window is closed
      
      elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1: # Left-click to place tower
          if self.placing_tower:
            if self.resources >= TOWER_COST:
              position = pygame.mouse.get_pos() # Get the mouse position
              self.towers.append(Tower(position)) # Add new tower
              self.resources -= TOWER_COST # Subtract the cost from resources
              self.placing_tower = False # Exit placement mode
            else:
              print(f"Insufficient resources.\
                    Current resources: {self.resources}")
          else:
            print("Not in tower placement mode.")
        elif event.button == 3: # Right-click to cancel tower placement
          self.placing_tower = False # Exit placement mode
      elif event.type == pygame.MOUSEMOTION:
        if self.placing_tower:
          self.cursor_position = pygame.mouse.get_pos() # Update the cursor position
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t: # Press 'T' to reset the game
          self.placing_tower = True
  
  def spawn_enemies(self):
    current_time = time.time()
    # Chech if more enemies need to be spawned for the current wave
    if self.enemies_spawned < ENEMIES_PER_WAVE * self.wave_number:
      # Spawn enemy if enough time has passed since last spawn
      if current_time - self.last_enemy_spawn_time > 1 / ENEMY_SPAWN_RATE:
        self.enemies.append(Enemy(self.path)) # Add new enemy
        self.enemies_spawned += 1
        self.last_enemy_spawn_time = current_time # Update the last spawn time
    elif not self.enemies:
      # Prepare for next wave when all enemies of current wave are defeated
      self.wave_number += 1
      self.enemies_spawned = 0
      
  def update_entities(self):
    # Update all towers
    for tower in self.towers:
      tower.update(self.enemies, self.bullets) 
    
    #Update all enemies
    for enemy in self.enemies[:]:
      enemy.update()
      if enemy.health <= 0:
        self.enemies.remove(enemy) # Remove dead enemies
        self.enemies_killed += 1
        self.resources += 10 # Reward for killing enemy
      elif enemy.reached_end:
        self.enemies.remove(enemy) # Remove enemy that reached the end
        # Implement lives or health deduction here
        
      # Continue updating entities
      for bullet in self.bullets[:]:
        bullet.update() # Update bullet position
        if bullet.target.health <= 0 or not bullet.is_alive:
          self.bullets.remove(bullet) 
          # Remove bullet if target dead or bullet is not alive
          # Create an explosion at the bullet's last position
          self.explosions.append(Explosion(bullet.position))
      
      # Update explosions and remove them when done
      for explosion in self.explosions[:]:
        explosion.update() # Update explosion animation
        if explosion.finished:
          self.explosions.remove(explosion)
          # Remove explosion when animation is finished
          
  def render(self):
    self.screen.fill(BACKGROUND_COLOR) #Clear the screen with background color
    self.draw_path() # Draw the enemy path
    if self.placing_tower and self.tower_preview_pos:
      self.draw_tower_preview(self.tower_preview_pos)
      # Draw tower preview when placing
    for tower in self.towers:
      tower.draw(self.screen) # Draw all towers
    for enemy in self.enemies:
      enemy.draw(self.screen) # Draw all enemies
    for bullet in self.bullets:
      bullet.draw(self.screen) # Draw all bullets
    for explosion in self.explosions:
      explosion.draw(self.screen) # Draw all explosions
    self.draw_hud() # Draw the heads-up display
    pygame.display.flip() # Update the full display surface to the screen
    
  def draw_path(self):
    # Draw a thicker and smoother path
    path_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
    # Create transparent surface
    pygame.draw.lines(path_surface, PATH_COLOR, False, self.path, 8)
    # Draw thicker path
    path_surface = pygame.transform.smoothscale\
      (path_surface, self.screen.get_size())
    # Smooth path
    self.screen.blit(path_surface, (0, 0)) # Draw the path surface onto the screen
    
  def draw_tower_preview(self, position):
    # Draw preview for the tower (a circle with a small barrel and range indicator)
    pygame.draw.circle(self.screen, TOWER_COLOR, position, 20, 1) # Tower base
    barrel_end = (position[0] + 30, position[1]) # Calculate barrel end position
    pygame.draw.line(self.screen, TOWER_COLOR, position, barrel_end, 2)
    # Tower barrel
    self.draw_dotted_circle(self.screen, TOWER_COLOR, position, TOWER_RANGE, 1)
    # Show as dotted circle
    
  def draw_dotted_circle(self, surface, color, center, radius, width):
    # Draw a dotted circle with the given radius, center, and color.
    for angle in range(0, 360, 10): # 10-degree increments for dotted effect
      x = center[0] + int(radius * math.cos(math.radians(angle)))
      # Calculate x position
      y = center[1] + int(radius * math.sin(math.radians(angle)))
      # Calculate y position
      pygame.draw.circle(surface, color, (x,y), width)
      # Draw small circle at calculated position
      
  def draw_hud(self):
    elapsed_time = int(time.time() - self.start_time) # Calculate elapsed time
    hud_texts = [
      f"Resources: {self.resources}"
      f"Wave: {self.wave_number}"
      f"Enemies Killed: {self.enemies_killed}"
      f"Time Elapsed: {elapsed_time}"
    ]
    for i, text in enumerate(hud_texts):
      text_surface = HUD_FONT.render(text, True, HUD_TEXT_COLOR) # Render text
      self.screen.blit(text_surface, (10, 10 + i * 25)) # Draw text on screen
      
  def check_game_over(self):
    # Implement game over conditions as needed pass
    pass

class Tower:
  def __init__(self, position):
    self.position = position # Tower's position
    self.range = TOWER_RANGE # Tower's attack range
    self.damage = TOWER_DAMAGE # Tower's damage per shot
    self.fire_rate = TOWER_FIRE_RATE # Time of last shot
    self.angle = 0 # Initial angle for rotation
  
  def update( self, enemies, bullets):
    current_time = time.time()
    if current_time - self.last_shot_time >=1 / self.fire_rate:
      target = self.get_target(enemies) # Find a target
      if target:
        bullets.append(Bullet(self.position)) # Create new bullet
        self.last_shot_time = current_time # Update last shot time
        
        # Instantly rotate the tower's angle to face the target
        self.angle = math.degrees(math.atan2(
          target.position[1] - self.position[1],
          target.position[0] - self.position[0]
        ))
  
  def get_target(self, enemies):
    for enemy in enemies:
      if calculate_distance(self.position, enemy.position) <= self.range:
        return enemy # Return the first enemy in range
    return None # Return none if no enemies in range
  
  def draw(self, screen):
    # Draw the tower (a circle with a small barrel)
    pygame.draw.circle(screen, TOWER_COLOR, self.position, 20) # Draw tower base
    
    # Calculate the end point of the barrel based on the tower's angle
    barrel_end = (self.position[0] + 40 * math.cos(math.radians(self.angle)),
                  self.position [1] + 40 * math.sin(math.radians(self.angle)))
    
    pygame.draw.line(screen, TOWER_COLOR, self.position, barrel_end, 4)
    # Draw the barrel (a line)
    
class Enemy:
  def __init__(self, path):
    self.path = path # The path the enemy will follow
    self.path_index = 0 # Current index in the path
    self.position = list(self.path[0]) # Start at the beginning of the path
    self.speed = ENEMY_SPEED # Enemy's movement speed
    self.health = ENEMY_HEALTH # Enemy's health
    self.reached_end = False # Flag to check if the enemy reached the end
    self.alpha = 0 # For fade-in effect (transparency)
    
  def update (self):
    # Fade-in effect
    if self.alpha < 255:
      self.alpha += 5 # Gradualy increase opacity
    
    if self.path_index < len(self.path) - 1:
      target_pos = self.path[self.path_index + 1] # Next point in the path
      direction = [target_pos[0] - self.position[0],
                   target_pos[1] - self.position[1]]
      distance = math.hypot(*direction) # Calculate distance to next point
      if distance <= self.speed:
        self.position = list(target_pos) # Move to next point
        self.path_index += 1 # Move to next path segment
      else:
        # Move towards the next point
        direction = [d / distance for d in direction]
        # Normalize direction
        self.position[0] += direction[0] * self.speed
        self.position[1] += direction[1] * self.speed
    else:
      self.reached_end = True
      # Fade-out effect before reaching the end
      self.alpha -= 5
      if self.alpha <= 0:
        self.alpha = 0
        self.reached_end = True # Mark as reached the end for removal
        
  def draw(self, screen):
    # Draw the enemy with fading transparency
    enemy_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    # Create a transparent surface
    enemy_surface.set_alpha(self.alpha) # Set transparency of the surface
    pygame.draw.circle(enemy_surface, ENEMY_COLOR, (15,15), 15)
    # Draw enemy on the surface
    screen.blit(enemy_surface, (self.position[0] - 15, self.position[1] - 15))
    # Draw the surface on the screen
    
    # Health bar
    health_bar_length = 30
    health_ratio = self.health / ENEMY_HEALTH
    # Draw red background of health bar
    pygame.draw.rect(screen, (255, 138, 138),\
                     [self.position[0] - 15, self.position[1]\
                       - 25, health_bar_length, 5])
    # Draw green part of health bar based on current health
    pygame.draw.rect(screen, \
                     (203, 226, 181), [self.position[0]\
                                      - 15, self.position[1]\
                                      - 25, health_bar_length * \
                                        health_ratio, 5])
    
class Bullet:
  def __init__(self, position, target):
    self.position = list(position) # Starting position of the bullet
    self.target = target # Target enemy
    self.speed = BULLET_SPEED # Speed of the bullet
    self.is_alive = True # Flag to check if bullet is still active
    
  def update(self):
    # Calculate direction towards the target
    direction = [self.target.position [0] \
                - self.position[0], self.target.position[1] \
                - self.position[1]]
    distance = math.hypot(*direction) # Calculate distance to target
    if distance <= self.speed:
      self.hit_target() # Hit the target if close enough
    else:
      # Move the bullet towards the target
      direction = [d / distance for d in direction] # normalize direction
      self.position[0] += direction[0] * self.speed
      self.position[1] += direction[1] * self.speed
  
  def hit_target(self):
    self.target.health -= TOWER_DAMAGE # Reduce target's health
    self.is_alive = False # Mark bullet as not alive
    
  def draw(self, screen):
    # Draw the bullet as a small circle
    pygame.draw.circle(screen, BULLET_COLOR, (int(self.position[0]), int(self.position
                        [1])), 5)
    
class Explosion:
  def __init__(self, position):
    self.position = position # Position of the explosion
    self.radius = 10 # Initial radius
    self.expansion_rate = 2 # How fast the explosion expands
    self.max_radius = 30 # Maximum radius of the explosion
    self.finished = False # Flag to check if explosion animation is finished
  
  def update(self):
    if self.radius < self.max_radius:
      self.radius += self.expansion_rate # Increase radius of the explosion
    else:
      self.finished = True # Mark explosion as finished
      
  def draw(self, screen):
    # Draw the explosion as a circle 
    pygame.draw.circle(screen, (255, 69, 0), self.position, self.radius)
    # Bright red-orande for explosion
    



    
    
        
        
    
      
      
  
    
              
              
