import pygame
import math



def scale_and_rotate(image_path, image_size=None, rotate=None):
    image = pygame.image.load(image_path)
    if image_size:
        image = pygame.transform.scale(image, image_size)
    if rotate:
        image = pygame.transform.rotate(image, rotate)
    return image.convert_alpha()


class SpriteSheet:
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame_x, frame_y, width=32, height=32, scale=2, colour=(0, 0, 0)):
        image = pygame.transform.scale(self.sheet.subsurface( ((frame_x * width), (frame_y * width), width, height)),
                                       (width * scale, height * scale))
        image.set_colorkey(colour)
        return image


def group_two_pass_collision(group1, group2, dokilla, dokillb):
    # Hits: first pass with simple collision, then 2nd pass with mask (mask is expensive)
    hits = pygame.sprite.groupcollide(group1, group2, False, False)
    if hits:
        new_group1 = pygame.sprite.Group()
        new_group2 = pygame.sprite.Group()
        for g1_hit, g2_hits in hits.items():
            new_group1.add(g1_hit)
            for element in g2_hits:
                new_group2.add(element)
        return pygame.sprite.groupcollide(group1, group2, dokilla, dokillb, pygame.sprite.collide_mask)


def sprite_two_pass_collision(sprite, group, dokill):
    hits = pygame.sprite.spritecollide(sprite, group, False)
    if hits:
        new_group = pygame.sprite.Group(hits)
        return pygame.sprite.spritecollide(sprite, new_group, dokill, pygame.sprite.collide_mask)

def unit_vector(x1, y1, x2, y2, scale=1):
    dx = x2 - x1
    dy = y2 - y1
    amp = math.sqrt(dx ** 2 + dy ** 2)
    return scale * dx / amp, scale * dy / amp
