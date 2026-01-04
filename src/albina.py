from logging import root
import os
import json
import random
import time
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext, messagebox
import threading
from datetime import datetime
import hashlib
from tkinter.font import Font
from turtle import bgcolor

class AlbinaGame:
    def __init__(self):
        # Инициализация игры
        self.version = "Albina V1"
        self.running = True
        self.server_running = False
        self.game_loaded = False
        self.current_world = None
        self.day_length = 60  # 60 секунд на игровой день
        self.selected_item = None
        self.plugins = []
        self.mob_difficulty = 0

        # Предметы в игре
        self.item_types = {
            "clothes": {
                "ushanka": {"name": "Ushanka", "effect": {"sleep_rate": -0.2}, "rarity": 0.3},
                "leather_jacket": {"name": "Leather Jacket", "effect": {"snake_damage": -0.2}, "rarity": 0.3},
                "striped_pants": {"name": "Striped Pants", "effect": {"hunger_rate": -0.2}, "rarity": 0.3},
                "croc_shoes": {"name": "Crocodile Shoes", "effect": {"move_speed": 0.1}, "rarity": 0.1},
            },
            "food": {
                "vodka": {"name": "Vodka", "hunger": -50, "rarity": 0.1},
                "bread": {"name": "Bread", "hunger": -35, "rarity": 0.4},
                "pickles": {"name": "Pickles", "hunger": -30, "rarity": 0.5},
                "potato": {"name": "Potato", "hunger": -10, "rarity": 0.7},
                "resin": {"name": "Resin", "hunger": -5, "rarity": 0.8},
                "bones": {"name": "Bones", "hunger": -1, "rarity": 0.6},
                "cockroach": {"name": "Cockroach", "hunger": -2, "rarity": 0.9}
            },
            "special": {
                "pingpong": {"name": "Ping Pong Ball", "effect": {"ping": True}, "rarity": 0.2},
                "wires": {"name": "Wires", "effect": {"craft": True}, "rarity": 0.4},
                "backpack": {"name": "Backpack", "effect": {"capacity": 15}, "rarity": 0.1}
            }
        }

        # Мобы в игре
        self.mob_types = {
            "snake": {"name": "Snake", "hp": 5, "damage": 3, "rarity": 0.5},
            "rat": {"name": "Rat", "hp": 6, "damage": 2, "rarity": 0.4},
            "centipede": {"name": "Centipede", "hp": 10, "damage": 4, "rarity": 0.3},
            "cockroach": {"name": "Cockroach", "hp": 1, "damage": 0, "rarity": 0.8}
        }

        # Статистика игрока
        self.player = {
            "x": 0,
            "y": 0,
            "hp": 100,
            "sleep": 0,
            "hunger": 0,
            "exp": 0,
            "day": 1,
            "time": "morning",
            "inventory": [],
            "equipped": {
                "hat": None,
                "jacket": None,
                "pants": None,
                "shoes": None
            },
            "used": None,
            "killed_mobs": {},
            "collected_items": [],
            "start_time": time.time(),
            "inventory_capacity": 3,
            "kick_damage": 2
        }

        # Настройки мира
        self.world = {
            "seed": "",
            "layout": {},
            "items": [],
            "mobs": [],
            "discovered": {}
        }

        # Инициализация GUI
        self.init_gui()

        # Запуск сервера
        self.start_server()

        # Основной игровой цикл
        self.game_loop()
        self.update_status_bar()

    def init_gui(self):
        # Создание основного окна
        self.root = tk.Tk()
        self.root.configure(bg="#212121")
        self.root.title("Albina")
        self.root.geometry("800x600")

        # Статус бар
        self.status_bar = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#212121", fg="#00ff00", font=("Consolas", 9, "bold"))
        self.status_bar.pack(fill=tk.X)

        # Консоль вывода
        self.console = scrolledtext.ScrolledText(self.root, state='disabled')
        self.console.configure(bg="#212121", fg="#00ff00", insertbackground="#aeada7", font=("Consolas", 12, "bold"))
        self.console.pack(fill=tk.BOTH, expand=True)

        # Фрейм для ввода команд
        self.input_frame = tk.Frame(self.root, bg="#212121")
        self.input_frame.pack(fill=tk.X)

        # Метка ">"
        self.prompt = tk.Label(self.input_frame, text=">", fg="#00ff00", bg="#212121")
        self.prompt.pack(side=tk.LEFT)

        # Поле ввода команд
        self.command_entry = tk.Entry(self.input_frame, bg="#212121", fg="#00ff00", insertbackground="#aeada7", font=("Consolas", 12, "bold"))
        self.command_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.command_entry.bind("<Return>", self.process_command)

        # Вывод начального сообщения
        self.print_to_console(self.version)
        self.root.after(2000, self.check_server)

    def print_to_console(self, text):
        self.console.configure(state='normal')
        self.console.insert(tk.END, text + "\n")
        self.console.configure(state='disabled')
        self.console.see(tk.END)

    def update_status_bar(self):
        status_text = f"Coordinates: ({self.player['x']}, {self.player['y']}) | " \
                     f"Day: {self.player['day']} | Time: {self.player['time']} | " \
                     f"H/S/G: {self.player['hp']}/{self.player['sleep']}/{self.player['hunger']} | " \
                     f"EXP: {self.player['exp']}"
        self.status_bar.config(text=status_text)
        self.root.after(1000, self.update_status_bar)

    def check_server(self):
        # Проверка и инициализация сервера
        if not os.path.exists("server"):
            os.makedirs("server")
            self.print_to_console("Created server directory")

        if not os.path.exists("server/config.cfg"):
            with open("server/config.cfg", "w") as f:
                json.dump({"port": 8080, "autosave": True}, f)
            self.print_to_console("Created default config file")

        # Проверка папки plugins
        if not os.path.exists("plugins"):
            os.makedirs("plugins")
            self.print_to_console("Created plugins directory")

        self.server_running = True
        self.print_to_console("Local server started")
        self.print_to_console("Type 'load' to load a world")

    def process_command(self, event):
        command = self.command_entry.get().strip().lower()
        self.command_entry.delete(0, tk.END)
        self.print_to_console(f"> {command}")

        if not self.game_loaded:
            # Команды главного меню
            if command.startswith("load"):
                self.load_world(int(command.split()[1]))
            elif command.startswith("new"):
                self.create_world(command.split()[1])
            elif command == "exit":
                self.quit_game()
            elif command == "help":
                self.print_to_console("Albina says: no one will help you")
            elif command == "credits":
                self.print_to_console(self.version)
            elif command == "stop":
                self.stop_server()
            elif command == "start":
                self.start_server()
            elif command == "kill":
                self.game_over("You committed suicide")
            else:
                self.print_to_console("Unknown command. Type 'load' to start")
        else:
            # Игровые команды
            if command in ["up", "down", "left", "right"]:
                self.move_player(command)
            elif command == "inventory":
                self.show_inventory()
            elif command.startswith("select"):
                self.select_item(command)
            elif command == "eat":
                self.eat_item()
            elif command == "sleep":
                self.sleep()
            elif command == "ping":
                self.ping()
            elif command == "kick":
                self.kick()
            elif command == "save":
                self.save_game()
            elif command == "give":
                self.give_item()
            elif command == "cloth":
                self.show_equipped()
            elif command.startswith("set"):
                self.equip_item()
            elif command.startswith("unset"):
                self.unequip_item()
            elif command == "use":
                self.use_item()
            elif command == "plugin":
                self.list_plugins()
            elif command == "exit":
                self.confirm_exit()
            else:
                self.print_to_console("Unknown command")

    def load_world(self, index):
        if not os.path.exists("world"):
            os.makedirs("world")
            self.print_to_console("Created world directory")
            self.print_to_console("No worlds available")
            return

        worlds = [d for d in os.listdir("world") if os.path.isdir(os.path.join("world", d))]
        if not worlds:
            self.print_to_console("No worlds available")
            return

        self.print_to_console("Available worlds:")
        for i, world in enumerate(worlds, 1):
            self.print_to_console(f"{i}. {world}")

        self.print_to_console("Enter world number to load:")

        # В реальной реализации нужно ожидать ввода пользователя
        self.load_specific_world(worlds[index - 1])

    def load_specific_world(self, world_name):
        world_path = os.path.join("world", world_name)
        if not os.path.exists(world_path):
            self.print_to_console(f"World {world_name} not found")
            return

        # Загрузка данных мира
        server_file = os.path.join(world_path, "server.alb")
        stat_file = os.path.join(world_path, "stat.alb")

        if os.path.exists(server_file):
            try:
                with open(server_file, "r") as f:
                    world_data = json.load(f)
                    self.world.update(world_data)

                    # Генерация мира на основе seed
                    self.generate_world()

                    self.current_world = world_name
                    self.game_loaded = True

                    # Загрузка статистики игрока
                    if os.path.exists(stat_file):
                        with open(stat_file, "r") as f:
                            player_data = json.load(f)
                            self.player.update(player_data)

                    self.print_to_console(f"World {world_name} loaded")
                    self.print_to_console("Use commands: up, down, left, right to move")

                    # Проверка координат игрока
                    if abs(self.player["x"]) > 50000 or abs(self.player["y"]) > 50000:
                        self.game_over("You saw the light and came out. This is the end")
            except Exception as e:
                self.print_to_console(f"Error loading world data: {str(e)}")
        else:
            self.print_to_console("No world data found")

    def generate_world(self):
        # Генерация мира на основе seed
        if not self.world["seed"]:
            self.world["seed"] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))

        random.seed(hashlib.sha256(self.world["seed"].encode()).hexdigest())

        # Простая генерация лабиринта
        # В реальной реализации нужно сделать более сложную систему
        self.world["layout"] = {}
        self.world["items"] = []
        self.world["mobs"] = []

        # Генерация предметов
        for _ in range(random.randint(20, 50)):
            item_type = random.choice(list(self.item_types.keys()))
            item_subtype = random.choice(list(self.item_types[item_type].keys()))
            if random.random() < self.item_types[item_type][item_subtype]["rarity"]:
                self.world["items"].append({
                    "type": item_type,
                    "subtype": item_subtype,
                    "x": random.randint(-100, 100),
                    "y": random.randint(-100, 100)
                })

        # Генерация мобов
        for _ in range(random.randint(10, 30)):
            mob_type = random.choice(list(self.mob_types.keys()))
            if random.random() < self.mob_types[mob_type]["rarity"]:
                self.world["mobs"].append({
                    "type": mob_type,
                    "x": random.randint(-100, 100),
                    "y": random.randint(-100, 100),
                    "hp": self.mob_types[mob_type]["hp"]
                })

    def create_world(self, name):
        if not os.path.exists("world"):
            os.makedirs("world")

        os.mkdir(f"world/{name}")

        with open(f"world/{name}/server.alb", 'w', encoding="utf-8") as file:
            seed = random.randint(0, 99999999)

            data = f"""
            {{
              "seed": "{seed}",
              "layout": {{}},
              "items": [],
              "mobs": [],
              "discovered": {{}}
            }}
            """

            file.write(data)
            self.print_to_console(f"created world \"{name}\"")

    def move_player(self, direction):
        # Сохраняем предыдущие координаты
        old_x, old_y = self.player["x"], self.player["y"]

        # Обновляем координаты
        if direction == "up":
            self.player["y"] += 1
        elif direction == "down":
            self.player["y"] -= 1
        elif direction == "left":
            self.player["x"] -= 1
        elif direction == "right":
            self.player["x"] += 1

        # Проверяем, не столкнулся ли игрок со стеной
        if self.check_wall_collision():
            self.player["x"], self.player["y"] = old_x, old_y
            self.print_to_console("Dead end")
        else:
            self.print_to_console(f"Moved {direction}")
            self.check_position()

            # Проверка на увеличение сложности мобов
            if abs(self.player["x"]) > 100 + self.mob_difficulty * 100 or abs(self.player["y"]) > 100 + self.mob_difficulty * 100:
                self.mob_difficulty += 1
                self.print_to_console("You feel the darkness getting deeper...")

    def check_wall_collision(self):
        # Проверка столкновения со стеной на основе seed
        pos_key = f"{self.player['x']},{self.player['y']}"

        if pos_key not in self.world["discovered"]:
            # Генерация стены на основе seed и координат
            random.seed(hashlib.sha256((self.world["seed"] + pos_key).encode()).hexdigest())
            is_wall = random.random() < 0.3  # 30% шанс стены
            self.world["discovered"][pos_key] = {"wall": is_wall}

        return self.world["discovered"][pos_key]["wall"]

    def check_position(self):
        # Проверка предметов в текущей позиции
        pos_items = [item for item in self.world["items"]
                    if item["x"] == self.player["x"] and item["y"] == self.player["y"]]

        for item in pos_items:
            if item["type"] == "clothes":
                item_data = self.item_types["clothes"][item["subtype"]]
            elif item["type"] == "food":
                item_data = self.item_types["food"][item["subtype"]]
            else:
                item_data = self.item_types["special"][item["subtype"]]

            self.print_to_console(f"You found: {item_data['name']}")
            self.world["items"].remove(item)

            if len(self.player["inventory"]) < self.player["inventory_capacity"]:
                self.player["inventory"].append({
                    "type": item["type"],
                    "subtype": item["subtype"],
                    "name": item_data["name"]
                })
                self.print_to_console(f"{item_data['name']} added to inventory")
            else:
                self.print_to_console("Inventory full! Can't pick up item")

        # Проверка мобов в текущей позиции
        pos_mobs = [mob for mob in self.world["mobs"]
                   if mob["x"] == self.player["x"] and mob["y"] == self.player["y"]]

        for mob in pos_mobs:
            mob_data = self.mob_types[mob["type"]]
            self.print_to_console(f"You encountered a {mob_data['name']}! Use 'kick' to fight")

    def show_inventory(self):
        if not self.player["inventory"]:
            self.print_to_console("Inventory is empty")
            return

        self.print_to_console("Inventory:")
        for i, item in enumerate(self.player["inventory"], 1):
            self.print_to_console(f"{i}. {item['name']}")
        self.print_to_console("Use 'select <number>' to choose item")

    def select_item(self, command):
        try:
            parts = command.split()
            if len(parts) < 2:
                self.print_to_console("Usage: select <item_number>")
                return

            item_num = int(parts[1]) - 1
            if 0 <= item_num < len(self.player["inventory"]):
                self.selected_item = item_num
                self.print_to_console(f"Selected {self.player['inventory'][item_num]['name']}")
            else:
                self.print_to_console("Invalid item number")
        except ValueError:
            self.print_to_console("Invalid item number")

    def eat_item(self):
        if not hasattr(self, 'selected_item') or self.selected_item is None:
            self.print_to_console("No item selected")
            return

        selected = self.player["inventory"][self.selected_item]

        if selected["type"] == "food":
            food_data = self.item_types["food"][selected["subtype"]]
            self.player["hunger"] = max(0, self.player["hunger"] + food_data["hunger"])
            self.print_to_console(f"You ate {selected['name']}. Hunger: {self.player['hunger']}")
        else:
            self.print_to_console(f"You tried to eat {selected['name']}, but it's not food")

        self.player["inventory"].pop(self.selected_item)
        self.selected_item = None

    def sleep(self):
        if self.player["time"] == "night":
            self.print_to_console("You're already sleeping")
            return

        self.player["time"] = "night"
        self.player["sleep"] = 0
        self.player["day"] += 1
        self.player["exp"] += 10
        self.print_to_console("You fell asleep...")
        self.root.after(5000, self.wake_up)

    def wake_up(self):
        self.player["time"] = "morning"
        self.print_to_console("You woke up refreshed")
        self.print_to_console(f"Day {self.player['day']} begins")

    def ping(self):
        # Проверка, есть ли у игрока пинг-понг
        has_ping = any(item["subtype"] == "pingpong" for item in self.player["inventory"])

        if has_ping:
            self.print_to_console("pong")
        else:
            self.print_to_console("You need a ping pong ball for that")

    def kick(self):
        # Проверка мобов в текущей позиции
        pos_mobs = [mob for mob in self.world["mobs"]
                   if mob["x"] == self.player["x"] and mob["y"] == self.player["y"]]

        if not pos_mobs:
            self.print_to_console("Nothing to kick here")
            return

        mob = pos_mobs[0]
        mob_data = self.mob_types[mob["type"]]

        # Нанесение урона
        damage = self.player["kick_damage"] + self.mob_difficulty
        mob["hp"] -= damage
        self.print_to_console(f"You kicked {mob_data['name']} for {damage} damage")

        # Проверка смерти моба
        if mob["hp"] <= 0:
            self.world["mobs"].remove(mob)
            self.player["exp"] += 5
            self.player["kick_damage"] += 1

            # Запись убитого моба
            if mob["type"] not in self.player["killed_mobs"]:
                self.player["killed_mobs"][mob["type"]] = 0
            self.player["killed_mobs"][mob["type"]] += 1

            self.print_to_console(f"{mob_data['name']} defeated! +5 EXP")

            # Шанс выпадения предмета
            if random.random() < 0.3:
                self.generate_mob_drop(mob["type"])
        else:
            # Контратака моба
            mob_damage = max(1, mob_data["damage"] + self.mob_difficulty)
            self.player["hp"] -= mob_damage
            self.print_to_console(f"{mob_data['name']} hit you for {mob_damage} damage")

            if self.player["hp"] <= 0:
                self.game_over(f"You were killed by {mob_data['name']}")

    def generate_mob_drop(self, mob_type):
        if mob_type == "cockroach":
            item = {"type": "food", "subtype": "cockroach", "name": "Cockroach"}
            self.player["inventory"].append(item)
            self.print_to_console("You got a Cockroach from the corpse")
        elif random.random() < 0.5:
            item_type = random.choice(["food", "special"])
            item_subtype = random.choice(list(self.item_types[item_type].keys()))
            item = {
                "type": item_type,
                "subtype": item_subtype,
                "name": self.item_types[item_type][item_subtype]["name"]
            }
            self.player["inventory"].append(item)
            self.print_to_console(f"You got {item['name']} from the corpse")

    def show_equipped(self):
        self.print_to_console("Equipped items:")
        for slot, item in self.player["equipped"].items():
            if item:
                self.print_to_console(f"{slot.capitalize()}: {item['name']}")
            else:
                self.print_to_console(f"{slot.capitalize()}: Empty")

    def equip_item(self):
        if not hasattr(self, 'selected_item') or self.selected_item is None:
            self.print_to_console("No item selected")
            return

        item = self.player["inventory"][self.selected_item]

        if item["type"] != "clothes":
            self.print_to_console("You can only equip clothing items")
            return

        slot = None
        if item["subtype"] == "ushanka":
            slot = "hat"
        elif item["subtype"] == "leather_jacket":
            slot = "jacket"
        elif item["subtype"] == "striped_pants":
            slot = "pants"
        elif item["subtype"] == "croc_shoes":
            slot = "shoes"

        if slot:
            # Снимаем уже надетый предмет, если есть
            if self.player["equipped"][slot]:
                old_item = self.player["equipped"][slot]
                self.player["inventory"].append(old_item)
                self.print_to_console(f"Removed {old_item['name']}")

            # Надеваем новый предмет
            self.player["equipped"][slot] = item
            self.player["inventory"].pop(self.selected_item)
            self.selected_item = None
            self.print_to_console(f"You equipped {item['name']}")

            # Применяем эффекты предмета
            self.apply_item_effects()
        else:
            self.print_to_console("This item cannot be equipped")

    def unequip_item(self):
        parts = command.split()
        if len(parts) < 2:
            self.print_to_console("Usage: unset <slot>")
            return

        slot = parts[1].lower()
        if slot not in self.player["equipped"]:
            self.print_to_console("Invalid slot. Available slots: hat, jacket, pants, shoes")
            return

        if self.player["equipped"][slot]:
            item = self.player["equipped"][slot]
            if len(self.player["inventory"]) < self.player["inventory_capacity"]:
                self.player["inventory"].append(item)
                self.player["equipped"][slot] = None
                self.print_to_console(f"You unequipped {item['name']}")
                self.apply_item_effects()
            else:
                self.print_to_console("Inventory full! Can't unequip item")
        else:
            self.print_to_console(f"{slot.capitalize()} slot is already empty")

    def apply_item_effects(self):
        # Сбрасываем все эффекты
        self.player["inventory_capacity"] = 3
        self.player["kick_damage"] = 2

        item = self.player["used"]
        if item:
            item_data = self.item_types["special"][item["subtype"]]
            if "effect" in item_data:
                for effect, value in item_data["effect"].items():
                    if effect == "capacity":
                        self.player["inventory_capacity"] = value

        # Применяем эффекты от надетых предметов
        for slot, item in self.player["equipped"].items():
            if item:
                item_data = self.item_types["clothes"][item["subtype"]]
                if "effect" in item_data:
                    for effect, value in item_data["effect"].items():
                        if effect == "capacity":
                            self.player["inventory_capacity"] = value
                        elif effect == "sleep_rate":
                            pass  # Обрабатывается в игровом цикле
                        elif effect == "hunger_rate":
                            pass  # Обрабатывается в игровом цикле
                        elif effect == "snake_damage":
                            pass  # Обрабатывается при получении урона
                        elif effect == "move_speed":
                            pass  # Может влиять на скорость передвижения

    def use_item(self):
        if not hasattr(self, 'selected_item') or self.selected_item is None:
            self.print_to_console("No item selected")
            return

        item = self.player["inventory"][self.selected_item]

        if item["type"] != "special":
            self.print_to_console("You can only use special items")
            return

        if self.player["used"]:
            old_item = self.player["used"]
            self.player["inventory"].append(old_item)
            self.print_to_console(f"Removed {old_item['name']}")

        # Надеваем новый предмет
        self.player["used"] = item
        self.player["inventory"].pop(self.selected_item)
        self.selected_item = None
        self.print_to_console(f"You equipped {item['name']}")

        # Применяем эффекты предмета
        self.apply_item_effects()

    def save_game(self):
        if not self.game_loaded:
            self.print_to_console("No world loaded to save")
            return

        world_path = os.path.join("world", self.current_world)
        if not os.path.exists(world_path):
            os.makedirs(world_path)

        # Сохраняем данные мира
        with open(os.path.join(world_path, "server.alb"), "w") as f:
            json.dump({
                "seed": self.world["seed"],
                "layout": self.world["layout"],
                "items": self.world["items"],
                "mobs": self.world["mobs"],
                "discovered": self.world["discovered"]
            }, f)

        # Сохраняем статистику игрока
        with open(os.path.join(world_path, "stat.alb"), "w") as f:
            json.dump({
                "x": self.player["x"],
                "y": self.player["y"],
                "hp": self.player["hp"],
                "sleep": self.player["sleep"],
                "hunger": self.player["hunger"],
                "exp": self.player["exp"],
                "day": self.player["day"],
                "time": self.player["time"],
                "inventory": self.player["inventory"],
                "equipped": self.player["equipped"],
                "killed_mobs": self.player["killed_mobs"],
                "collected_items": self.player["collected_items"],
                "inventory_capacity": self.player["inventory_capacity"],
                "kick_damage": self.player["kick_damage"]
            }, f)

        self.print_to_console("Game saved")

    def game_over(self, message):
        self.print_to_console(f"Game Over: {message}")
        self.game_loaded = False
        self.current_world = None
        self.print_to_console("Type 'load' to start a new game")

    def game_loop(self):
        if self.game_loaded:
            # Обновляем состояние игрока
            self.player["hunger"] = min(100, self.player["hunger"] + 1)
            self.player["sleep"] = min(100, self.player["sleep"] + 0.5)

            # Проверяем голод
            if self.player["hunger"] >= 100:
                self.player["hp"] -= 5
                self.print_to_console("You're starving! -5 HP")

            # Проверяем сонливость
            if self.player["sleep"] >= 100:
                self.player["hp"] -= 2
                self.print_to_console("You're exhausted! -2 HP")

            # Проверяем здоровье
            if self.player["hp"] <= 0:
                self.game_over("You died from your wounds")

            # Смена времени суток
            current_time = time.time()
            day_progress = (current_time - self.player["start_time"]) % self.day_length
            if day_progress < self.day_length * 0.4:
                self.player["time"] = "morning"
            elif day_progress < self.day_length * 0.7:
                self.player["time"] = "day"
            elif day_progress < self.day_length * 0.9:
                self.player["time"] = "evening"
            else:
                self.player["time"] = "night"

        self.root.after(1000, self.game_loop)

    def load_plugins(self):
        """Загрузка плагинов из папки plugins"""
        if not os.path.exists("plugins"):
            os.makedirs("plugins")
            return

        self.plugins = []
        for filename in os.listdir("plugins"):
            if filename.endswith(".alb"):
                try:
                    with open(os.path.join("plugins", filename), "r") as f:
                        plugin_data = json.load(f)
                        plugin_data["enabled"] = True
                        self.plugins.append(plugin_data)
                        self.print_to_console(f"Loaded plugin: {plugin_data.get('name', 'Unnamed')}")
                except Exception as e:
                    self.print_to_console(f"Failed to load plugin {filename}: {str(e)}")

    def apply_plugin_effects(self):
        """Применение эффектов от активных плагинов"""
        for plugin in self.plugins:
            if plugin.get("enabled", False):
                # Применяем модификаторы предметов
                if "items" in plugin:
                    for item_type, items in plugin["items"].items():
                        if item_type not in self.item_types:
                            self.item_types[item_type] = {}
                        self.item_types[item_type].update(items)

                # Применяем модификаторы мобов
                if "mobs" in plugin:
                    for mob_name, mob_data in plugin["mobs"].items():
                        self.mob_types[mob_name] = mob_data

    def list_plugins(self):
        """Показать список всех плагинов"""
        if not self.plugins:
            self.print_to_console("No plugins available")
            return

        self.print_to_console("Available plugins:")
        for i, plugin in enumerate(self.plugins, 1):
            status = "ON" if plugin.get("enabled", False) else "OFF"
            self.print_to_console(f"{i}. {plugin.get('name', 'Unnamed')} [{status}]")
        self.print_to_console("Use 'plugin <number> on/off' to toggle plugins")

    def toggle_plugin(self, command):
        """Включить/выключить плагин"""
        parts = command.split()
        if len(parts) < 3:
            self.print_to_console("Usage: plugin <number> <on/off>")
            return

        try:
            plugin_num = int(parts[1]) - 1
            if 0 <= plugin_num < len(self.plugins):
                action = parts[2].lower()
                if action == "on":
                    self.plugins[plugin_num]["enabled"] = True
                    self.print_to_console(f"Plugin '{self.plugins[plugin_num].get('name', 'Unnamed')}' enabled")
                elif action == "off":
                    self.plugins[plugin_num]["enabled"] = False
                    self.print_to_console(f"Plugin '{self.plugins[plugin_num].get('name', 'Unnamed')}' disabled")
                else:
                    self.print_to_console("Invalid action. Use 'on' or 'off'")

                # Перезагружаем эффекты плагинов
                self.apply_plugin_effects()
            else:
                self.print_to_console("Invalid plugin number")
        except ValueError:
            self.print_to_console("Invalid plugin number")

    def generate_complex_maze(self):
        """Генерация более сложного лабиринта с использованием алгоритма recursive backtracking"""
        width, height = 100, 100  # Размер лабиринта
        maze = [[1 for _ in range(width)] for _ in range(height)]  # 1 = стена, 0 = проход

        # Начальная позиция
        x, y = random.randint(0, width-1), random.randint(0, height-1)
        maze[y][x] = 0
        stack = [(x, y)]

        # Направления движения
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while stack:
            x, y = stack[-1]
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = x + dx*2, y + dy*2

                if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 1:
                    maze[y + dy][x + dx] = 0
                    maze[ny][nx] = 0
                    stack.append((nx, ny))
                    break
            else:
                stack.pop()

        # Сохраняем лабиринт в мире
        for y in range(height):
            for x in range(width):
                pos_key = f"{x - width//2},{y - height//2}"
                self.world["discovered"][pos_key] = {"wall": maze[y][x] == 1}

    def give_item(self):
        """Команда give - получить случайный предмет (для тестирования)"""
        if len(self.player["inventory"]) >= self.player["inventory_capacity"]:
            self.print_to_console("Inventory full!")
            return

        item_type = random.choice(list(self.item_types.keys()))
        item_subtype = random.choice(list(self.item_types[item_type].keys()))
        item_data = self.item_types[item_type][item_subtype]

        self.player["inventory"].append({
            "type": item_type,
            "subtype": item_subtype,
            "name": item_data["name"]
        })
        self.print_to_console(f"You got: {item_data['name']}")

    def confirm_exit(self):
        """Подтверждение выхода из игры"""
        self.print_to_console("Are you sure you want to exit? 1: Yes, 2: No")
        # В реальной реализации нужно ожидать ввода пользователя
        # Для примера просто выходим
        self.quit_game()

    def quit_game(self):
        """Выход из игры"""
        if self.game_loaded:
            self.save_game()
        self.running = False
        self.root.destroy()

    def stop_server(self):
        """Остановка сервера"""
        self.print_to_console("Stop server? Unsaved changes will be lost. 1: Yes, 2: No")
        # В реальной реализации нужно ожидать ввода пользователя
        # Для примера просто останавливаем
        self.server_running = False
        self.print_to_console("Server stopped")

    def start_server(self):
        """Запуск сервера"""
        if not self.server_running:
            self.server_running = True
            self.print_to_console("Local server started")

    def run(self):
        """Основной цикл приложения"""
        # Загружаем плагины при старте
        self.load_plugins()
        self.apply_plugin_effects()

        # Запускаем GUI
        self.root.mainloop()

if __name__ == "__main__":
    game = AlbinaGame()
    game.run()
