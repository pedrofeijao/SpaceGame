import pygame


class SelectBox:
    def __init__(self, options, icons=None, top=200, left=600, width=900, height=800,
                 top_margin=100, option_size=120, option_spacing=60, left_margin=40, cycle_options=True):
        self.options = options
        self.icons = icons
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.top_margin = top_margin
        self.selected = 0
        self.cycle_options = cycle_options
        self.option_size = option_size
        self.option_spacing = option_spacing

        self.left_margin = left_margin


    def select_next(self):
        self.selected += 1
        if self.selected >= len(self.options):
            self.selected = 0 if self.cycle_options else len(self.options) - 1

    def select_previous(self):
        self.selected -= 1
        if self.selected < 0:
            self.selected = 0 if not self.cycle_options else len(self.options) - 1

    def get_selected(self):
        return self.options[self.selected]

    def draw(self, window: pygame.Surface, font):
        pygame.draw.rect(window, pygame.Color('gray'),
                         pygame.rect.Rect(self.left - 4, self.top - 4, self.width + 8, self.height + 8), border_radius= 10)
        pygame.draw.rect(window, pygame.Color('gray20'),
                         pygame.rect.Rect(self.left, self.top, self.width, self.height) , border_radius=10)

        icon_space = 100 if self.icons else 20
        for idx, option in enumerate(self.options):
            left = self.left + self.left_margin
            top = self.top + self.top_margin + (self.option_size + self.option_spacing) * idx
            pygame.draw.rect(window, pygame.Color('red') if self.selected == idx else pygame.Color('black'),
                             pygame.rect.Rect(left - 2, top - 2, 4 + self.width - 2 * self.left_margin, 4 + self.option_size), border_radius=8)
            pygame.draw.rect(window, pygame.Color('gray90') if self.selected == idx else pygame.Color('gray50'),
                             pygame.rect.Rect(left, top, self.width - 2 * self.left_margin, self.option_size), border_radius=8)
            txt = font.render(str(option), False, pygame.Color('darkblue') if self.selected == idx else pygame.Color('gray20'))
            rect = txt.get_rect(topleft=(left + icon_space, top + (self.option_size - font.get_height()) // 2))
            if self.icons:
                icon = self.icons[idx]
                window.blit(icon, (left + 20, top + (self.option_size - icon.get_height()) // 2))
            window.blit(txt, rect)
