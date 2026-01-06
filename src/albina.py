from enum import Enum
import os
import json
import random
import time
import tkinter as tk
from tkinter import scrolledtext
import hashlib
from typing import Callable

class State(Enum):
    MENU = 0
    GAME = 1

# class StandartUI(AlbinaUI):
#     def __init__()

class CommandHandler:
    def __init__(self, commands: dict[tuple[str, State], Callable]):
        self._commands: dict[tuple[str, State], Callable] = dict()

        for item, callback in commands.items():
            verb, state = item
            if callable(callback):
                self._commands[(verb.lower(), state)] = callback
            else:
                raise TypeError(f"Handler for {verb} isn't callable")

    def process_command(self, command: str, state: State):
        blocks = command.strip().lower().split()

        args = blocks[1:]

        first = blocks[0].lower()

        func = self._commands.get((first, state))

        if func:
            func(args)
        else:
            return f"Unknown command '{first}'"

class AlbinaGame:
    def __init__(self):
        self.version = "Albina V1.1"
        self.running = True
        self.server_running = False
        self.game_loaded = False
        self.current_world = None
        self.day_length = 300
        self.selected_item = None
        self.plugins = []
        self.mob_difficulty = 0
        self._state = State.MENU
        self.time = time.time()

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

        self.mob_types = {
            "snake": {"name": "Snake", "hp": 5, "damage": 3, "rarity": 0.5},
            "rat": {"name": "Rat", "hp": 6, "damage": 2, "rarity": 0.4},
            "centipede": {"name": "Centipede", "hp": 10, "damage": 4, "rarity": 0.3},
            "cockroach": {"name": "Cockroach", "hp": 1, "damage": 0, "rarity": 0.8}
        }

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
            "inventory_capacity": 3,
            "kick_damage": 2
        }

        self.world = {
            "seed": None,
            "layout": {},
            "items": [],
            "mobs": [],
            "discovered": {},
            "time": 0.0
        }

        commands = {
            ("worlds", State.MENU): self.worlds_list,
            ("load", State.MENU): self.load_command,
            ("new", State.MENU): self.new_world,
            ("exit", State.MENU): self.exit_command,
            ("help", State.MENU): self.help_command,
            ("credits", State.MENU): self.credits_command,
            ("stop", State.MENU): self.stop_command,
            ("start", State.MENU): self.start_command,
            ("exit", State.MENU): self.exit_command,  # noqa: F601

            ("up", State.GAME): self.up_command,
            ("down", State.GAME): self.down_command,
            ("left", State.GAME): self.left_command,
            ("right", State.GAME): self.right_command,
            ("inventory", State.GAME): self.show_inventory,
            ("give", State.GAME): self.give_item,
            ("select", State.GAME): self.select_item,
            ("kick", State.GAME): self.kick,
            ("eat", State.GAME): self.eat_item,
            ("sleep", State.GAME): self.sleep,
            ("ping", State.GAME): self.ping,
            ("cloth", State.GAME): self.show_equipped,
            ("equip", State.GAME): self.equip_item,
            ("unequip", State.GAME): self.unequip_item,
            ("use", State.GAME): self.use_item,
            ("save", State.GAME): self.save_game,
            ("kill", State.GAME): self.kill_command,
            ("plugin", State.GAME): self.list_plugins,
            ("exit", State.GAME): self.exit_game_mode
        }

        self.command_handler = CommandHandler(commands)

        self.init_gui()

        self.start_command(None)

        self.game_loop()
        self.update_status_bar()

    def init_gui(self):
        self.root = tk.Tk()
        self.root.configure(bg="#212121")
        self.root.title("Albina")
        self.root.geometry("1000x600")

        self.main_frame = tk.Frame(self.root, bg="#212121")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_panel = tk.Frame(self.main_frame, bg="#212121", width=700)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_panel.pack_propagate(False)

        self.right_panel = tk.Frame(self.main_frame, bg="#1a1a1a", width=300)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.right_panel.pack_propagate(False)

        self.status_bar = tk.Label(self.left_panel, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#212121", fg="#00ff00", font=("Consolas", 9, "bold"))
        self.status_bar.pack(fill=tk.X)

        self.console = scrolledtext.ScrolledText(self.left_panel, state='disabled')
        self.console.configure(bg="#212121", fg="#00ff00", insertbackground="#aeada7", font=("Consolas", 12, "bold"))
        self.console.pack(fill=tk.BOTH, expand=True)

        self.input_frame = tk.Frame(self.left_panel, bg="#212121")
        self.input_frame.pack(fill=tk.X)

        self.prompt = tk.Label(self.input_frame, text=">", fg="#00ff00", bg="#212121")
        self.prompt.pack(side=tk.LEFT)

        self.command_entry = tk.Entry(self.input_frame, bg="#212121", fg="#00ff00", insertbackground="#aeada7", font=("Consolas", 12, "bold"))
        self.command_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.command_entry.bind("<Return>", self.command_handle)

        self.init_right_panel()
        self.print_to_console(self.version)
        self.root.after(2000, self.check_server)

    def color_gui(self, color: str = "#00ff00", pos: str = "X"):
        self.status_bar.configure(fg=color)
        self.console.configure(fg=color)
        self.prompt.configure(fg=color)
        self.command_entry.configure(fg=color)
        self.time_label.configure(fg=color)
        self.inventory_label.configure(fg=color)
        self.compass_label.configure(fg=color)
        self.inventory_list.configure(fg=color)
        self.compas_color = color
        self.draw_compass(pos)

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

    def kill_command(self, _args):
        self.game_over("You committed suicide")

    def help_command(self, _args):
        self.print_to_console("Albina says: no one will help you")

    def credits_command(self, _args):
        self.print_to_console(self.version)

    def init_right_panel(self):
        self.compas_color = "#00ff00"
        self.time_label = tk.Label(self.right_panel, text="", fg="#00ff00", bg="#1a1a1a", font=("Consolas", 14, "bold"))
        self.time_label.pack(pady=10)

        self.inventory_label = tk.Label(self.right_panel, text="INVENTORY", fg="#00ff00", bg="#1a1a1a", font=("Consolas", 12, "bold"))
        self.inventory_label.pack(pady=5)

        self.inventory_list = tk.Listbox(self.right_panel, bg="#1a1a1a", fg="#00ff00", font=("Consolas", 10), height=10, relief=tk.FLAT, bd=0)
        self.inventory_list.pack(fill=tk.BOTH, expand=True, padx=10)

        self.compass_label = tk.Label(self.right_panel, text="COMPASS", fg="#00ff00", bg="#1a1a1a", font=("Consolas", 12, "bold"))
        self.compass_label.pack(pady=5)

        self.compass_canvas = tk.Canvas(self.right_panel, width=100, height=100, bg="#1a1a1a", highlightthickness=0)
        self.compass_canvas.pack(pady=10)

        self.draw_compass("X")
        self.update_right_panel()

    def update_right_panel(self):
        time_text = f"Day: {self.player['day']}\nTime: {self.player['time']}"
        self.time_label.config(text=time_text)

        self.inventory_list.delete(0, tk.END)
        for index, item in enumerate(self.player["inventory"], 1):
            self.inventory_list.insert(tk.END, f"{index}.{item['name']}")

        self.root.after(1000, self.update_right_panel)

    def draw_compass(self, direction):
        self.compass_canvas.delete("all")

        center_x, center_y = 50, 50
        radius = 40

        self.compass_canvas.create_oval(center_x-radius, center_y-radius, center_x+radius, center_y+radius, outline=self.compas_color, width=2)

        directions = {
            "N": (0, -30, "N"),
            "E": (30, 0, "E"),
            "S": (0, 30, "S"),
            "W": (-30, 0, "W"),
            "X": (0, 0, "Unknown")
        }

        for key, (dx, dy, text) in directions.items():
            x = center_x + dx
            y = center_y + dy
            color = self.compas_color if key == direction else "#555555"
            self.compass_canvas.create_text(x, y, text=text, fill=color, font=("Consolas", 10, "bold"))

    def check_server(self):
        if not os.path.exists("server"):
            os.makedirs("server")
            self.print_to_console("Created server directory")

        if not os.path.exists("server/config.cfg"):
            with open("server/config.cfg", "w") as f:
                json.dump({"port": 8080, "autosave": True}, f)
            self.print_to_console("Created default config file")

        if not os.path.exists("plugins"):
            os.makedirs("plugins")
            self.print_to_console("Created plugins directory")

        self.server_running = True
        self.print_to_console("Local server started")
        self.print_to_console("Type 'load' to load a world")

    def command_handle(self, _event):
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)
        self.print_to_console(f"> {command}")

        traceback = self.command_handler.process_command(command, self._state)

        if traceback:
            self.print_to_console(traceback)

    def worlds(self) -> list[str] | None:
        if not os.path.exists("world"):
            os.makedirs("world")
            self.print_to_console("Created worlds directory")
            return None

        worlds = [d for d in os.listdir("world") if os.path.isdir(os.path.join("world", d))]

        if worlds:
            return worlds
        else:
            return None

    def worlds_list(self, _args):
        worlds = self.worlds()

        if worlds:
            self.print_to_console("Available worlds:")
            for i, world in enumerate(worlds, 1):
                self.print_to_console(f"{i}. {world}")

            self.print_to_console("type 'load <index>' to load world")
        else:
            self.print_to_console("No available worlds")
            self.print_to_console("type 'new <name>' to create new world")

    def load_command(self, args: list[str]):
        index = int(args[0])

        worlds = self.worlds()

        if worlds:
            self.load_specific_world(worlds[index - 1])
        else:
            self.print_to_console("type 'new <name>' to create new world")

    def load_specific_world(self, world_name):
        world_path = os.path.join("world", world_name)

        if not os.path.exists(world_path):
            self.print_to_console(f"World {world_name} not found")
            return

        server_file = os.path.join(world_path, "server.alb")
        stat_file = os.path.join(world_path, "stat.alb")

        if os.path.exists(server_file):
            try:
                with open(server_file, 'r', encoding="utf-8") as f:
                    world_data = json.load(f)
                    self.world.update(world_data)

            except Exception as e:
                self.print_to_console(f"Error loading world data: {e}")
                return

            self.current_world = world_name
            self._state = State.GAME
            self.game_loaded = True

        else:
            self.print_to_console("No world data found")
            return

        if os.path.exists(stat_file):
            try:
                with open(stat_file, "r", encoding="utf-8") as f:
                    player_data = json.load(f, parse_int=None)
                    self.player.update(player_data)
            except Exception as e:
                self.print_to_console(f"Error loading world data: {e}")
                return

        else:
            self.print_to_console("No world data found")
            return

        self.print_to_console(f"World {world_name} loaded")
        self.print_to_console("Use commands: up, down, left, right to move")

        if abs(self.player["x"]) > 50000 or abs(self.player["y"]) > 50000:
            self.game_over("You saw the light and came out. This is the end")

    def generate_world(self):
        data = dict()

        data["seed"] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))

        random.seed(hashlib.sha256(data["seed"].encode()).hexdigest())

        data["layout"] = {}
        data["items"] = []
        data["mobs"] = []

        for _ in range(random.randint(10000, 15000)):
            item_type = random.choice(list(self.item_types.keys()))
            item_subtype = random.choice(list(self.item_types[item_type].keys()))
            if random.random() < self.item_types[item_type][item_subtype]["rarity"]:
                data["items"].append({
                    "type": item_type,
                    "subtype": item_subtype,
                    "x": random.randint(-100, 100),
                    "y": random.randint(-100, 100)
                })

        for _ in range(random.randint(5000, 10000)):
            mob_type = random.choice(list(self.mob_types.keys()))
            if random.random() < self.mob_types[mob_type]["rarity"]:
                data["mobs"].append({
                    "type": mob_type,
                    "x": random.randint(-100, 100),
                    "y": random.randint(-100, 100),
                    "hp": self.mob_types[mob_type]["hp"]
                })

        return data

    def new_world(self, args: list[str]):
        name = args[0]

        if not os.path.exists("world"):
            os.makedirs("world")

        os.mkdir(f"world/{name}")

        with open(f"world/{name}/stat.alb", 'w', encoding="utf-8") as file:
            data = {
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

            json.dump(data, file)

        with open(f"world/{name}/server.alb", 'w', encoding="utf-8") as file:
            data = self.generate_world()

            json.dump(data, file)

        self.print_to_console(f"created world \"{name}\"")

    def up_command(self, _args):
        self.move_player("up")

    def down_command(self, _args):
        self.move_player("down")

    def left_command(self, _args):
        self.move_player("left")

    def right_command(self, _args):
        self.move_player("right")

    def move_player(self, direction: str):
        self.player["sleep"] = min(100, self.player["sleep"] + 1)
        old_x, old_y = self.player["x"], self.player["y"]

        if direction == "up":
            self.player["y"] += 1
        elif direction == "down":
            self.player["y"] -= 1
        elif direction == "left":
            self.player["x"] -= 1
        elif direction == "right":
            self.player["x"] += 1

        if self.check_wall_collision():
            self.player["x"], self.player["y"] = old_x, old_y
            self.color_gui("blue")
            self.print_to_console("Dead end")
        else:
            self.print_to_console(f"Moved {direction}")

            if abs(self.player["x"]) > 100 + self.mob_difficulty * 100 or abs(self.player["y"]) > 100 + self.mob_difficulty * 100:
                self.mob_difficulty += 1
                self.print_to_console("You feel the darkness getting deeper...")

                pos = "X"
                if direction == "up":
                    pos = "N"
                elif direction == "right":
                    pos = "E"
                elif direction == "down":
                    pos = "S"
                elif direction == "left":
                    pos = "W"

                self.check_position(pos)

    def check_wall_collision(self):
        pos_key = f"{self.player['x']},{self.player['y']}"

        if pos_key not in self.world["discovered"]:
            random.seed(hashlib.sha256((self.world["seed"] + pos_key).encode()).hexdigest())
            is_wall = random.random() < 0.3
            self.world["discovered"][pos_key] = {"wall": is_wall}

        return self.world["discovered"][pos_key]["wall"]

    def check_position(self, pos: str):
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

        pos_mobs = [mob for mob in self.world["mobs"]
                   if mob["x"] == self.player["x"] and mob["y"] == self.player["y"]]

        if pos_mobs:
            self.color_gui("red")
        else:
            self.root.after(1000, self.color_gui, "#00ff00", pos)

        for mob in pos_mobs:
            mob_data = self.mob_types[mob["type"]]
            self.print_to_console(f"You encountered a {mob_data['name']}! Use 'kick' to fight")

    def show_inventory(self, _args):
        if not self.player["inventory"]:
            self.print_to_console("Inventory is empty")
            return

        self.print_to_console("Inventory:")
        for i, item in enumerate(self.player["inventory"], 1):
            self.print_to_console(f"{i}. {item['name']}")
        self.print_to_console("Use 'select <number>' to choose item")

    def select_item(self, args: list[str]):
        try:

            if len(args) < 1:
                self.print_to_console("Usage: select <item_number>")
                return

            item_num = int(args[0]) - 1
            if 0 <= item_num < len(self.player["inventory"]):
                self.selected_item = item_num
                self.print_to_console(f"Selected {self.player['inventory'][item_num]['name']}")
            else:
                self.print_to_console("Invalid item number")
        except ValueError:
            self.print_to_console("Invalid item number")

    def eat_item(self, _args):
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

    def sleep(self, _args):
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

    def ping(self, _args):
        has_ping = any(item["subtype"] == "pingpong" for item in self.player["inventory"])

        if has_ping:
            self.print_to_console("pong")
        else:
            self.print_to_console("You need a ping pong ball for that")

    def kick(self, _args):
        pos_mobs = [mob for mob in self.world["mobs"]
                   if mob["x"] == self.player["x"] and mob["y"] == self.player["y"]]

        if not pos_mobs:
            self.print_to_console("Nothing to kick here")
            return

        self.player["sleep"] = min(100, self.player["sleep"] + 5)
        mob = pos_mobs[0]
        mob_data = self.mob_types[mob["type"]]

        damage = self.player["kick_damage"] + self.mob_difficulty
        mob["hp"] -= damage
        self.print_to_console(f"You kicked {mob_data['name']} for {damage} damage")

        if mob["hp"] <= 0:
            self.world["mobs"].remove(mob)
            self.player["exp"] += 5
            self.player["kick_damage"] += 1
            self.color_gui()

            if mob["type"] not in self.player["killed_mobs"]:
                self.player["killed_mobs"][mob["type"]] = 0
            self.player["killed_mobs"][mob["type"]] += 1

            self.print_to_console(f"{mob_data['name']} defeated! +5 EXP")

            if random.random() < 0.3:
                self.generate_mob_drop(mob["type"])
        else:
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

    def show_equipped(self, _args):
        self.print_to_console("Equipped items:")
        for slot, item in self.player["equipped"].items():
            if item:
                self.print_to_console(f"{slot.capitalize()}: {item['name']}")
            else:
                self.print_to_console(f"{slot.capitalize()}: Empty")

    def equip_item(self, _args):
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
            if self.player["equipped"][slot]:
                old_item = self.player["equipped"][slot]
                self.player["inventory"].append(old_item)
                self.print_to_console(f"Removed {old_item['name']}")

            self.player["equipped"][slot] = item
            self.player["inventory"].pop(self.selected_item)
            self.selected_item = None
            self.print_to_console(f"You equipped {item['name']}")

            self.apply_item_effects()
        else:
            self.print_to_console("This item cannot be equipped")

    def unequip_item(self, args: list[str]):
        if len(args) < 1:
            self.print_to_console("Usage: unset <slot>")
            return

        slot = args[0].lower()
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
        self.player["inventory_capacity"] = 3
        self.player["kick_damage"] = 2

        item = self.player["used"]
        if item:
            item_data = self.item_types["special"][item["subtype"]]
            if "effect" in item_data:
                for effect, value in item_data["effect"].items():
                    if effect == "capacity":
                        self.player["inventory_capacity"] = value

        for _slot, item in self.player["equipped"].items():
            if item:
                item_data = self.item_types["clothes"][item["subtype"]]
                if "effect" in item_data:
                    for effect, value in item_data["effect"].items():
                        if effect == "capacity":
                            self.player["inventory_capacity"] = value
                        elif effect == "sleep_rate":
                            pass
                        elif effect == "hunger_rate":
                            pass
                        elif effect == "snake_damage":
                            pass
                        elif effect == "move_speed":
                            pass

    def use_item(self, _args):
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

        self.player["used"] = item
        self.player["inventory"].pop(self.selected_item)
        self.selected_item = None
        self.print_to_console(f"You equipped {item['name']}")

        self.apply_item_effects()

    def save_game(self, _args):
        if self._state != State.GAME:
            self.print_to_console("No world loaded to save")
            return

        world_path = os.path.join("world", str(self.current_world))
        if not os.path.exists(world_path):
            os.makedirs(world_path)

        with open(os.path.join(world_path, "server.alb"), "w") as f:
            json.dump(self.world, f)

        with open(os.path.join(world_path, "stat.alb"), "w") as f:
            json.dump(self.player, f)

        self.print_to_console("Game saved")

    def game_over(self, message):
        self.save_game(None)
        self.print_to_console(f"Game Over: {message}")
        self.game_loaded = False
        self._state = State.MENU
        self.current_world = None
        self.print_to_console("Type 'load' to start a new game")

    def game_loop(self):
        if self.game_loaded:
            self.player["hunger"] = min(100, self.player["hunger"] + 0.125)
            self.player["sleep"] = min(100, round(self.player["sleep"] + 0.1, 2))

            if self.player["hunger"] >= 100:
                self.player["hp"] -= 5
                self.print_to_console("You're starving! -5 HP")

            if self.player["sleep"] >= 100:
                self.player["hp"] -= 2
                self.print_to_console("You're exhausted! -2 HP")

            if self.player["hp"] <= 0:
                self.game_over("You died from your wounds")


            current_time = time.time()
            self.world["time"] += current_time - self.time
            self.time = current_time

            day_progress = self.world["time"] % self.day_length
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
                if "items" in plugin:
                    for item_type, items in plugin["items"].items():
                        if item_type not in self.item_types:
                            self.item_types[item_type] = {}
                        self.item_types[item_type].update(items)

                if "mobs" in plugin:
                    for mob_name, mob_data in plugin["mobs"].items():
                        self.mob_types[mob_name] = mob_data

    def list_plugins(self, _args):
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

                self.apply_plugin_effects()
            else:
                self.print_to_console("Invalid plugin number")
        except ValueError:
            self.print_to_console("Invalid plugin number")

    def generate_complex_maze(self):
        """Генерация более сложного лабиринта с использованием алгоритма recursive backtracking"""
        width, height = 100, 100
        maze = [[1 for _ in range(width)] for _ in range(height)]

        x, y = random.randint(0, width-1), random.randint(0, height-1)
        maze[y][x] = 0
        stack = [(x, y)]

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

        for y in range(height):
            for x in range(width):
                pos_key = f"{x - width//2},{y - height//2}"
                self.world["discovered"][pos_key] = {"wall": maze[y][x] == 1}

    def give_item(self, _args):
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

    def exit_game_mode(self, _args):
        self.save_game(None)

        self.game_loaded = False
        self.current_world = None
        self._state = State.MENU

    def confirm_exit(self, _args):
        """Подтверждение выхода из игры"""
        self.print_to_console("Are you sure you want to exit? 1: Yes, 2: No")

        self.exit_command(None)

    def exit_command(self, _args):
        """Выход из игры"""
        if self.game_loaded:
            self.save_game(None)
        self.running = False
        self.root.destroy()

    def stop_command(self, _args):
        """Остановка сервера"""
        self.print_to_console("Stop server? Unsaved changes will be lost. 1: Yes, 2: No")

        self.server_running = False
        self.print_to_console("Server stopped")

    def start_command(self, _args):
        """Запуск сервера"""
        if not self.server_running:
            self.server_running = True

    def run(self):
        """Основной цикл приложения"""

        self.load_plugins()
        self.apply_plugin_effects()

        self.root.mainloop()

if __name__ == "__main__":
    game = AlbinaGame()
    game.run()
