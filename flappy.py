import pygame
import sys
import random
import os
import math

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game Constants
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.25
FLAP_STRENGTH = -5
PIPE_SPEED_START = 3
PIPE_GAP_START = 150
PIPE_FREQUENCY_START = 1800  # milliseconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 180, 0)
BLUE = (0, 0, 255)
SKY_BLUE = (135, 206, 235)
SUNSET_COLORS = [(135, 206, 235), (255, 175, 100), (70, 70, 90)]  # Day, sunset, night

# Bird colors - New vibrant color palette
BIRD_BODY_COLOR = (255, 191, 0)       # Golden yellow
BIRD_WING_COLOR = (255, 127, 39)      # Orange
BIRD_BELLY_COLOR = (255, 223, 128)    # Light yellow
BIRD_BEAK_COLOR = (255, 80, 0)        # Bright orange
BIRD_EYE_COLOR = (50, 50, 50)         # Dark gray for eye

# Game variables
score = 0
high_score = 0
game_over = False
last_pipe_time = 0
difficulty_level = 1
pipe_speed = PIPE_SPEED_START
pipe_gap = PIPE_GAP_START
pipe_frequency = PIPE_FREQUENCY_START
time_of_day = 0  # 0: day, 1: sunset, 2: night
day_night_cycle = 0

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

# Load sounds
try:
    flap_sound = pygame.mixer.Sound("sounds/flap.wav")
    score_sound = pygame.mixer.Sound("sounds/score.wav")
    hit_sound = pygame.mixer.Sound("sounds/hit.wav")
    
    # Set sound volumes
    flap_sound.set_volume(0.3)
    score_sound.set_volume(0.3)
    hit_sound.set_volume(0.3)
    
    # Load background music
    pygame.mixer.music.load("sounds/background_music.mp3")
    pygame.mixer.music.set_volume(0.2)
    
    sounds_loaded = True
except:
    sounds_loaded = False
    
# Create sounds directory if it doesn't exist
os.makedirs("sounds", exist_ok=True)

# Create the background
background_width = WIDTH * 3
background = pygame.Surface((background_width, HEIGHT))
clouds = []
for _ in range(15):
    cloud_x = random.randint(0, background_width - 1)
    cloud_y = random.randint(0, HEIGHT // 2)
    cloud_size = random.randint(30, 70)
    clouds.append((cloud_x, cloud_y, cloud_size))

# Create layers for parallax scrolling
mountains = []
for i in range(background_width // 100 + 1):
    mountain_x = i * 100
    mountain_height = random.randint(50, 150)
    mountains.append((mountain_x, mountain_height))

# Bird class
class Bird:
    def __init__(self):
        self.x = 50
        self.y = HEIGHT // 2
        self.velocity = 0
        self.width = 40  # Slightly larger bird
        self.height = 34  # Slightly taller bird
        self.alive = True
        self.flap_animation = 0
        self.rotation = 0
        self.flap_time = 0
        self.wing_angle = 0
        self.eye_blink_timer = random.randint(50, 150)  # Random blink timing
        self.blinking = False
        self.blink_duration = 5
        self.color_variation = random.randint(-15, 15)  # Slight color variation
        
    def flap(self):
        self.velocity = FLAP_STRENGTH
        self.flap_animation = 15  # Longer animation
        self.flap_time = pygame.time.get_ticks()
        self.wing_angle = 30  # Wing up position
        if sounds_loaded:
            flap_sound.play()
    
    def update(self):
        # Apply gravity
        self.velocity += GRAVITY
        self.y += self.velocity
        
        # Calculate rotation based on velocity (smoother transition)
        target_rotation = max(-30, min(self.velocity * 3, 90))
        self.rotation = self.rotation * 0.9 + target_rotation * 0.1  # Smooth rotation
        
        # Keep bird in bounds
        if self.y < 0:
            self.y = 0
            self.velocity = 0
        if self.y > HEIGHT - self.height - 20:  # Account for ground
            self.y = HEIGHT - self.height - 20
            self.velocity = 0
            self.alive = False  # Bird hits the ground
            if sounds_loaded:
                hit_sound.play()
        
        # Update flap animation with smoother transitions
        if self.flap_animation > 0:
            self.flap_animation -= 1
            # Calculate wing angle based on animation progress
            if self.flap_animation > 10:
                self.wing_angle = 30 - (15 - self.flap_animation) * 3  # Wing moving up
            else:
                self.wing_angle = 30 - (10 - self.flap_animation) * 6  # Wing moving down
        else:
            # Gentle wing motion when not actively flapping
            self.wing_angle = 10 + math.sin(pygame.time.get_ticks() / 200) * 5
            
        # Handle eye blinking
        self.eye_blink_timer -= 1
        if self.eye_blink_timer <= 0:
            if not self.blinking:
                self.blinking = True
                self.blink_duration = 5
            else:
                self.blinking = False
                self.eye_blink_timer = random.randint(100, 200)
                
        if self.blinking:
            self.blink_duration -= 1
            if self.blink_duration <= 0:
                self.blinking = False
                self.eye_blink_timer = random.randint(100, 200)
    
    def draw(self):
        # Prepare bird surface for rotation with transparent background
        bird_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        
        # Adjust colors based on variation
        body_color = tuple(max(0, min(255, c + self.color_variation)) for c in BIRD_BODY_COLOR)
        wing_color = tuple(max(0, min(255, c + self.color_variation)) for c in BIRD_WING_COLOR)
        belly_color = tuple(max(0, min(255, c + self.color_variation)) for c in BIRD_BELLY_COLOR)
        
        # Draw body (shifted to allow for beak)
        center_x, center_y = self.width // 2 - 2, self.height // 2
        body_rect = pygame.Rect(0, 0, self.width - 5, self.height)
        pygame.draw.ellipse(bird_surface, body_color, body_rect)
        
        # Draw belly/chest (lighter color)
        belly_rect = pygame.Rect(5, self.height // 3, self.width // 2, self.height // 2)
        pygame.draw.ellipse(bird_surface, belly_color, belly_rect)
        
        # Draw wing with animation
        # Calculate wing position based on animation
        wing_x = 2
        wing_y = self.height // 2 - 5 + self.wing_angle // 3
        wing_width = self.width // 2
        wing_height = 10 + abs(self.wing_angle) // 3
        
        # Create wing shape
        wing_points = [
            (wing_x, wing_y + wing_height // 2),
            (wing_x + wing_width // 2, wing_y - self.wing_angle // 3),
            (wing_x + wing_width, wing_y + wing_height // 2)
        ]
        pygame.draw.polygon(bird_surface, wing_color, wing_points)
        
        # Add detail to wing
        detail_points = [
            (wing_x + 3, wing_y + wing_height // 2 - 1),
            (wing_x + wing_width // 2, wing_y - self.wing_angle // 3 + 2),
            (wing_x + wing_width - 3, wing_y + wing_height // 2 - 1)
        ]
        pygame.draw.polygon(bird_surface, tuple(c-30 for c in wing_color), detail_points)
        
        # Draw tail feathers
        tail_points = [
            (3, self.height // 2 - 3),
            (0, self.height // 2 - 8),
            (5, self.height // 2 - 12),
            (10, self.height // 2 - 5)
        ]
        pygame.draw.polygon(bird_surface, wing_color, tail_points)
        
        # Draw eye
        if not self.blinking:
            # White of eye
            pygame.draw.circle(bird_surface, WHITE, (self.width - 12, self.height // 3), 7)
            # Pupil
            pygame.draw.circle(bird_surface, BIRD_EYE_COLOR, (self.width - 10, self.height // 3), 4)
            # Highlight
            pygame.draw.circle(bird_surface, WHITE, (self.width - 11, self.height // 3 - 2), 2)
        else:
            # Closed eye - just a line
            pygame.draw.line(bird_surface, BIRD_EYE_COLOR, 
                            (self.width - 16, self.height // 3), 
                            (self.width - 8, self.height // 3), 2)
        
        # Draw beak
        beak_points = [
            (self.width - 5, self.height // 2 - 2),
            (self.width + 5, self.height // 2 - 4),
            (self.width + 5, self.height // 2 + 2),
            (self.width - 5, self.height // 2 + 4)
        ]
        pygame.draw.polygon(bird_surface, BIRD_BEAK_COLOR, beak_points)
        
        # Draw beak division line
        pygame.draw.line(bird_surface, (200, 60, 0), 
                        (self.width, self.height // 2 - 1),
                        (self.width + 5, self.height // 2), 2)
        
        # Add crest/top feathers for style
        for i in range(3):
            feather_x = self.width - 15 - i * 4
            feather_y = self.height // 4 - 2 - i
            feather_size = 5 - i
            pygame.draw.circle(bird_surface, tuple(max(0, c-20) for c in body_color), 
                              (feather_x, feather_y), feather_size)
        
        # Rotate bird
        rotated_bird = pygame.transform.rotate(bird_surface, -self.rotation)
        bird_rect = rotated_bird.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        
        # Draw bird with rotation
        screen.blit(rotated_bird, bird_rect.topleft)
        
        # Add shadow for depth (only when bird is above ground)
        if self.y < HEIGHT - self.height - 30:
            shadow_y = HEIGHT - 25
            shadow_size = max(5, 20 - (HEIGHT - 25 - self.y) // 20)
            shadow_alpha = max(30, 120 - (HEIGHT - 25 - self.y) // 5)
            shadow_surface = pygame.Surface((shadow_size * 2, shadow_size), pygame.SRCALPHA)
            shadow_color = (0, 0, 0, shadow_alpha)
            pygame.draw.ellipse(shadow_surface, shadow_color, (0, 0, shadow_size * 2, shadow_size))
            screen.blit(shadow_surface, (self.x + self.width//2 - shadow_size, shadow_y - shadow_size//2))
    
    def get_rect(self):
        # Create a slightly smaller hitbox for more forgiving gameplay
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 12, self.height - 10)

# Pipe class
class Pipe:
    def __init__(self):
        self.gap_y = random.randint(100, HEIGHT - 120 - pipe_gap)
        self.x = WIDTH
        self.width = 50
        self.passed = False
        self.pipe_color = (0, 180, 0)
        self.cap_color = (0, 150, 0)
        
        # For special pipes
        self.is_golden = random.random() < 0.1  # 10% chance of golden pipe
        if self.is_golden:
            self.pipe_color = (255, 215, 0)
            self.cap_color = (218, 165, 32)
    
    def update(self):
        self.x -= pipe_speed
    
    def draw(self):
        # Draw top pipe
        pygame.draw.rect(screen, self.pipe_color, (self.x, 0, self.width, self.gap_y))
        # Draw bottom pipe
        pygame.draw.rect(screen, self.pipe_color, (self.x, self.gap_y + pipe_gap, self.width, HEIGHT - self.gap_y - pipe_gap - 20))
        
        # Add pipe caps
        pygame.draw.rect(screen, self.cap_color, (self.x - 3, self.gap_y - 20, self.width + 6, 20))
        pygame.draw.rect(screen, self.cap_color, (self.x - 3, self.gap_y + pipe_gap, self.width + 6, 20))
    
    def get_rects(self):
        top_pipe = pygame.Rect(self.x, 0, self.width, self.gap_y)
        bottom_pipe = pygame.Rect(self.x, self.gap_y + pipe_gap, self.width, HEIGHT - self.gap_y - pipe_gap - 20)
        return top_pipe, bottom_pipe
    
    def is_offscreen(self):
        return self.x < -self.width

# Particle class for visual effects
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 6)
        self.velocity_x = random.uniform(-2, 2)
        self.velocity_y = random.uniform(-3, -1)
        self.lifetime = random.randint(30, 90)
    
    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.1  # Gravity effect
        self.lifetime -= 1
        self.size = max(0, self.size - 0.05)
    
    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))
    
    def is_dead(self):
        return self.lifetime <= 0 or self.size <= 0

# Drawing functions
def draw_background():
    # Fill the sky with appropriate color based on time of day
    if time_of_day == 0:  # Day
        sky_color = SUNSET_COLORS[0]
    elif time_of_day == 1:  # Sunset
        sky_color = SUNSET_COLORS[1]
    else:  # Night
        sky_color = SUNSET_COLORS[2]
    
    screen.fill(sky_color)
    
    # Draw stars at night
    if time_of_day == 2:
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT // 2)
            size = random.randint(1, 3)
            brightness = random.randint(200, 255)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
    
    # Draw clouds with parallax effect
    cloud_color = (255, 255, 255) if time_of_day == 0 else (200, 180, 180) if time_of_day == 1 else (100, 100, 120)
    for cloud in clouds:
        cloud_x = cloud[0] % background_width
        cloud_x -= background_scroll * 0.2  # Slower parallax for clouds
        cloud_x %= WIDTH
        pygame.draw.circle(screen, cloud_color, (int(cloud_x), cloud[1]), cloud[2])
    
    # Draw mountains with parallax effect
    mountain_color = (100, 100, 100) if time_of_day == 0 else (80, 60, 60) if time_of_day == 1 else (40, 40, 50)
    for mountain in mountains:
        mountain_x = mountain[0] % background_width
        mountain_x -= background_scroll * 0.5  # Medium parallax for mountains
        mountain_x %= (WIDTH + 100)
        mountain_x -= 100
        if mountain_x < WIDTH:
            pygame.draw.polygon(screen, mountain_color, [
                (mountain_x, HEIGHT - 20),
                (mountain_x + 60, HEIGHT - 20 - mountain[1]),
                (mountain_x + 120, HEIGHT - 20)
            ])

def draw_ground():
    ground_color = (150, 75, 0) if time_of_day == 0 else (120, 60, 0) if time_of_day == 1 else (50, 30, 0)
    pygame.draw.rect(screen, ground_color, (0, HEIGHT - 20, WIDTH, 20))
    
    # Draw grass
    grass_color = (0, 160, 0) if time_of_day == 0 else (0, 130, 0) if time_of_day == 1 else (0, 70, 0)
    for i in range(0, WIDTH, 5):
        grass_height = random.randint(2, 6)
        pygame.draw.line(screen, grass_color, (i, HEIGHT - 20), (i, HEIGHT - 20 - grass_height), 2)

def draw_ui():
    # Draw score
    score_text = font.render(f"Score: {score}", True, BLACK if time_of_day == 0 else WHITE)
    screen.blit(score_text, (10, 10))
    
    # Draw high score
    high_score_text = font.render(f"High: {high_score}", True, BLACK if time_of_day == 0 else WHITE)
    screen.blit(high_score_text, (WIDTH - high_score_text.get_width() - 10, 10))
    
    # Draw difficulty level
    level_text = font.render(f"Level: {difficulty_level}", True, BLACK if time_of_day == 0 else WHITE)
    screen.blit(level_text, (10, 50))

def update_difficulty():
    global difficulty_level, pipe_speed, pipe_gap, pipe_frequency
    
    # Update difficulty based on score
    new_level = 1 + score // 10
    if new_level > difficulty_level:
        difficulty_level = new_level
        pipe_speed = PIPE_SPEED_START + (difficulty_level - 1) * 0.2
        pipe_gap = max(PIPE_GAP_START - (difficulty_level - 1) * 5, 100)
        pipe_frequency = max(PIPE_FREQUENCY_START - (difficulty_level - 1) * 100, 1200)

def update_day_night_cycle():
    global time_of_day, day_night_cycle
    
    # Update day/night cycle every 30 seconds
    day_night_cycle += 1
    if day_night_cycle >= 30 * FPS:
        day_night_cycle = 0
        time_of_day = (time_of_day + 1) % 3

# Create game objects
bird = Bird()
pipes = []
particles = []
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
background_scroll = 0

# Game states
game_active = False
start_screen = True

# Start the background music if sounds are loaded
if sounds_loaded:
    pygame.mixer.music.play(-1)  # -1 to loop indefinitely

# Game loop
running = True

while running:
    current_time = pygame.time.get_ticks()
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                if start_screen:
                    start_screen = False
                    game_active = True
                    last_pipe_time = current_time
                elif game_over:
                    # Reset game
                    bird = Bird()
                    pipes = []
                    particles = []
                    score = 0
                    last_pipe_time = current_time
                    game_over = False
                    game_active = True
                    difficulty_level = 1
                    pipe_speed = PIPE_SPEED_START
                    pipe_gap = PIPE_GAP_START
                    pipe_frequency = PIPE_FREQUENCY_START
                elif game_active:
                    bird.flap()
            # Mute/unmute sound
            if event.key == pygame.K_m and sounds_loaded:
                if pygame.mixer.music.get_volume() > 0:
                    pygame.mixer.music.set_volume(0)
                    flap_sound.set_volume(0)
                    score_sound.set_volume(0)
                    hit_sound.set_volume(0)
                else:
                    pygame.mixer.music.set_volume(0.2)
                    flap_sound.set_volume(0.3)
                    score_sound.set_volume(0.3)
                    hit_sound.set_volume(0.3)
    
    # Update background scroll
    background_scroll += 1
    if background_scroll >= background_width:
        background_scroll = 0
    
    # Update day/night cycle
    if game_active and not game_over:
        update_day_night_cycle()
    
    # Draw background
    draw_background()
    
    if start_screen:
        # Draw bird
        bird.update()  # Update for animation even on start screen
        bird.draw()
        
        # Draw animated title
        title_text = font.render("FLAPPY BIRD", True, BLACK if time_of_day == 0 else WHITE)
        bob_offset = math.sin(pygame.time.get_ticks() / 300) * 5
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3 + bob_offset))
        
        # Flash instruction text
        if (pygame.time.get_ticks() // 500) % 2:
            instruction_text = font.render("Press SPACE to start", True, BLACK if time_of_day == 0 else WHITE)
            screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2))
        
        # Draw controls
        controls_text = small_font.render("SPACE/UP: Flap   M: Mute sound", True, BLACK if time_of_day == 0 else WHITE)
        screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT // 2 + 40))
        
        # Draw ground
        draw_ground()
    
    elif game_active and not game_over:
        # Update difficulty
        update_difficulty()
        
        # Update bird
        bird.update()
        
        # Create new pipes
        if current_time - last_pipe_time > pipe_frequency:
            pipes.append(Pipe())
            last_pipe_time = current_time
        
        # Update pipes
        for pipe in pipes[:]:
            pipe.update()
            
            # Check for scoring
            if not pipe.passed and pipe.x + pipe.width < bird.x:
                pipe.passed = True
                score += 1 if not pipe.is_golden else 3  # Golden pipes worth 3 points
                if sounds_loaded:
                    score_sound.play()
                
                # Create score particles
                for _ in range(15):  # More particles
                    color = (255, 215, 0) if pipe.is_golden else (255, 255, 0)
                    particles.append(Particle(bird.x, bird.y, color))
                
            # Remove off-screen pipes
            if pipe.is_offscreen():
                pipes.remove(pipe)
            
            # Check for collisions
            top_pipe, bottom_pipe = pipe.get_rects()
            if bird.get_rect().colliderect(top_pipe) or bird.get_rect().colliderect(bottom_pipe):
                game_over = True
                if sounds_loaded:
                    hit_sound.play()
                if score > high_score:
                    high_score = score
                # Create collision particles
                for _ in range(30):  # More particles for explosion effect
                    particles.append(Particle(bird.x, bird.y, (255, 100, 100)))
        
        # Check if bird hit the ground or went out of bounds
        if bird.y >= HEIGHT - bird.height - 20 or bird.y <= 0:
            game_over = True
            if score > high_score:
                high_score = score
        
        # Update particles
        for particle in particles[:]:
            particle.update()
            if particle.is_dead():
                particles.remove(particle)
        
        # Draw pipes
        for pipe in pipes:
            pipe.draw()
        
        # Draw particles
        for particle in particles:
            particle.draw()
        
        # Draw bird
        bird.draw()
        
        # Draw ground
        draw_ground()
        
        # Draw UI
        draw_ui()
    
    elif game_over:
        # Draw pipes
        for pipe in pipes:
            pipe.draw()
        
        # Draw particles
        for particle in particles:
            particle.update()
            particle.draw()
        
        # Draw bird
        bird.draw()
        
        # Draw ground
        draw_ground()
        
        # Draw game over screen
        game_over_text = font.render("GAME OVER", True, BLACK if time_of_day == 0 else WHITE)
        score_text = font.render(f"Score: {score}", True, BLACK if time_of_day == 0 else WHITE)
        high_score_text = font.render(f"High Score: {high_score}", True, BLACK if time_of_day == 0 else WHITE)
        restart_text = font.render("Press SPACE to restart", True, BLACK if time_of_day == 0 else WHITE)
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 30))
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2))
        
        # Flash restart text
        if (pygame.time.get_ticks() // 500) % 2:
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 40))
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()