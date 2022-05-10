import pygame
import requests
import os
import sys

from geo import geocode
from bus import find_business


LAT_STEP = 0.002
LON_STEP = 0.002


class MapParams():
    def __init__(self):
        self.lat = 55.729738
        self.lon = 37.664777
        self.zoom = 15
        self.type = "map"
        
    def ll(self):
        return "{0},{1}".format(self.lon, self.lat)

    def update(self, event):
        if event.key == pygame.K_PAGEUP  and self.zoom < 19:
            self.zoom += 1
        elif event.key == pygame.K_PAGEDOWN  and self.zoom > 2:
            self.zoom -= 1
        elif event.key == pygame.K_LEFT:
            self.lon -= LON_STEP * pow(2, 15 - self.zoom)
        elif event.key == pygame.K_RIGHT:
            self.lon += LON_STEP * pow(2, 15 - self.zoom)
        elif event.key == pygame.K_UP:
            self.lat += LAT_STEP * pow(2, 15 - self.zoom)
        elif event.key == pygame.K_DOWN:
            self.lat -= LAT_STEP * pow(2, 15 - self.zoom)


def load_map(mp):
    map_params = {
        "ll": mp.ll(),
        "z": mp.zoom,
        "l": mp.type
    }

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)
        
    if not response:
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)

    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)

    return map_file


def main():

    pygame.init()
    screen = pygame.display.set_mode((600, 450))

    mp = MapParams()

    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            break
        elif event.type == pygame.KEYUP:
            mp.update(event)
        map_file = load_map(mp)
        screen.blit(pygame.image.load(map_file), (0, 0))
        pygame.display.flip()
    pygame.quit()
    os.remove(map_file)


if __name__ == "__main__":
    main()
