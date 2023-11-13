import discord
import asyncio
from discord.ext import commands
import requests
import json
import time

# Definizione delle regioni
REGIONI = {
    1: "Kanto",
    2: "Johto",
    3: "Hoenn",
    4: "Sinnoh",
    5: "Unova",
    6: "Kalos",
    7: "Alola",
    8: "Galar",
    9: "Paldea",
    10: "Special"
}

# Numero massimo di Pokémon in ciascuna generazione
MAX_POKEMON_PER_GENERATION = [151, 251, 386, 493, 649, 721, 809, 898, 1020, 10500]  # Aggiunto un valore massimo per l'ottava generazione

# Mappa dei tipi ai colori desiderati
COLORI_PER_TIPO = {
    "normal": discord.Color(0xC3C3B5),  # Grigio
    "fighting": discord.Color(0x7D1F1A),  # Rosso scuro
    "flying": discord.Color(0x87CEEB),  # Azzurro chiaro
    "poison": discord.Color(0x914E8B),  # Viola scuro
    "ground": discord.Color(0xD2B48C),  # Marrone
    "rock": discord.Color(0x8B795E),  # Grigio scuro
    "bug": discord.Color(0x6A8C5A),  # Verde scuro
    "ghost": discord.Color(0x553774),  # Viola scuro
    "steel": discord.Color(0xB0C4DE),  # Blu chiaro
    "fire": discord.Color(0xFF4500),  # Rosso
    "water": discord.Color(0x3399FF),  # Blu
    "grass": discord.Color(0x77DD77),  # Verde chiaro
    "electric": discord.Color(0xFFD700),  # Giallo
    "psychic": discord.Color(0xFF1493),  # Rosa scuro
    "ice": discord.Color(0x87CEFA),  # Azzurro chiaro
    "dragon": discord.Color(0x7038F8),  # Viola chiaro
    "dark": discord.Color(0x705848),  # Marrone scuro
    "fairy": discord.Color(0xFF69B4),  # Rosa
    "unknown": discord.Color(0xA9A9A9),  # Grigio chiaro
    "shadow": discord.Color(0x555555),  # Grigio scuro
}

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command('help')  # Rimuove il comando di aiuto predefinito
ultima_ora_comando = {}

def ora_attuale():
    return int(time.time())

def ev_yield(nome_pokemon):
    url = f'https://pokeapi.co/api/v2/pokemon/{nome_pokemon.lower()}'
    risposta = requests.get(url)

    if risposta.status_code == 200:
        dati_pokemon = risposta.json()
        ev_yields = dati_pokemon.get('stats', [])
        ev_yield_values = [f"{stat['effort']} {stat['stat']['name'].capitalize()}" for stat in ev_yields]
        return ev_yield_values
    else:
        return None

def ottieni_info_pokemon(nome_pokemon, forma=None):
    url = f'https://pokeapi.co/api/v2/pokemon/{nome_pokemon.lower()}'
    
    risposta = requests.get(url)
    
    if risposta.status_code == 200:
        dati_pokemon = risposta.json()

        # Se una forma è specificata, cerca la sua variante tra le varietà
        if forma:
            for varieta in dati_pokemon.get('varieties', []):
                if varieta['is_default'] and varieta['pokemon']['name'].endswith(forma.lower()):
                    # Trovata la variante della forma
                    url_variante = varieta['pokemon']['url']
                    risposta_variante = requests.get(url_variante)
                    
                    if risposta_variante.status_code == 200:
                        dati_pokemon = risposta_variante.json()
                        break
        
        return dati_pokemon
    else:
        return None

def debolezze_di_tipo(nome_tipo):
    url = f'https://pokeapi.co/api/v2/type/{nome_tipo.lower()}'
    risposta = requests.get(url)
    
    if risposta.status_code == 200:
        dati_tipo = risposta.json()
        debolezze = dati_tipo['damage_relations']['double_damage_from']
        return [d['name'].capitalize() for d in debolezze]
    else:
        return None

def ottieni_regione_da_pokedex(num_pokedex):
    for generazione, max_pokemon in enumerate(MAX_POKEMON_PER_GENERATION, start=1):
        if num_pokedex <= max_pokemon:
            return REGIONI[generazione]
    return "Unknown"

def colore_per_tipo(tipo):
    return COLORI_PER_TIPO.get(tipo.lower(), discord.Color.default())

@bot.event
async def on_ready():
    print(f'Bot connesso come {bot.user.name}')

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        await message.channel.send("Zekrom is the best 'mon of them all. Written by: Zekrom himself... Why are you even seeing this?")
    
    await bot.process_commands(message)

@bot.tree.command(name="infopokemon", description="Shows detailed informations on a Pokémon.")
async def infopokemon(interaction: discord.Interaction, nome_pokemon: str, forma: str = None):
    try:
        await interaction.response.defer()

        # Aggiungi una variabile per tenere traccia dello stato del comando
        successo = False


        # Ottieni l'ID dell'utente che ha inviato il comando
        utente_id = interaction.user.id
        # Ottieni l'ora attuale
        ora_corrente = ora_attuale()
        # Verifica se sono passati almeno 10 secondi dall'ultima richiesta dell'utente
        if utente_id in ultima_ora_comando and ora_corrente - ultima_ora_comando[utente_id] < 10:
            await interaction.response.send_message("Slow down! You have to wait at least 10 seconds in between commands.")
            return

        # Aggiorna l'ora dell'ultimo comando per l'utente corrente
        ultima_ora_comando[utente_id] = ora_corrente
        # Ottieni dati base del Pokémon
        dati_pokemon = ottieni_info_pokemon(nome_pokemon, forma)

        if dati_pokemon:
            # Crea un nuovo oggetto discord.Embed per ogni interazione
            embed = discord.Embed()  # Imposta il campo description
            # Ottieni le debolezze di tipo
            messaggio_debolezze = ""
            for tipo_info in dati_pokemon['types']:
                if isinstance(tipo_info, dict):
                    tipo = tipo_info['type']['name'].capitalize()
                    debolezze_tipo = debolezze_di_tipo(tipo)
                    if debolezze_tipo:
                        messaggio_debolezze += f"\n**{tipo}**: Weak to {', '.join(debolezze_tipo)}"
                    else:
                        messaggio_debolezze += f"\nImpossible to fetch any info on {tipo}"

        

            # Ottieni le EV (Effort Values)
            ev_yield_values = ev_yield(nome_pokemon)

            # Aggiungi le EV all'embed solo se sono disponibili
            if ev_yield_values:
                # Aggiungi gli EV all'embed
                embed.add_field(name="EV Yield", value=f"{', '.join(ev_yield_values)}", inline=False)
            else:
                # Se gli EV non sono disponibili, aggiungi un campo con il link specifico
                ev_link = "https://pokemondb.net/ev/all"
                embed.add_field(name="EV", value=f"For further information about EV's, get to [this page]({ev_link})", inline=False)

            # Ottieni le statistiche del Pokémon
            statistiche = f"\n\n\n{nome_pokemon}'s Stats:"
            for stat in dati_pokemon['stats']:
                nome_stat = stat['stat']['name'].capitalize()
                statistiche += f"\n**{nome_stat}**: {stat['base_stat']}"

            # Ottieni le abilità del Pokémon
            abilita = f"\n\n\n{nome_pokemon}'s Abilities:"
            for ability in dati_pokemon['abilities']:
                abilita += f"\n**{ability['ability']['name'].capitalize()}**"

                # Aggiungi link esterno per spiegare l'abilità
                abilita_link = f"https://pokemondb.net/ability/{ability['ability']['name'].lower()}"
                abilita += f" [Explanation]({abilita_link})"

            # Ottieni altre informazioni come numero Pokèdex
            num_pokedex = dati_pokemon['id']

            # Ottieni peso e altezza del Pokémon
            peso_kg = dati_pokemon['weight'] / 10  # Converti in kg
            altezza_m = dati_pokemon['height'] / 10  # Converti in metri

            # Ottieni la regione del Pokémon
            regione_pokemon = ottieni_regione_da_pokedex(num_pokedex)

            # Verifica se l'URL dell'immagine è valido
            immagine_url = dati_pokemon['sprites']['front_default']

            if immagine_url and immagine_url.startswith(('http://', 'https://')):
                embed.title = f"Informations about {nome_pokemon}"
                embed.set_image(url=immagine_url)

                # Aggiungi le debolezze di tipo all'embed
                embed.description = messaggio_debolezze

                # Aggiungi le statistiche del Pokémon all'embed
                embed.add_field(name="Stats", value=statistiche, inline=False)

                # Aggiungi le abilità del Pokémon all'embed
                embed.add_field(name="Abilities", value=abilita, inline=False)

                # Aggiungi altre informazioni come numero Pokèdex, peso, altezza, regione
                embed.add_field(name="Pokèdex Num.", value=num_pokedex, inline=True)
                embed.add_field(name="Weight", value=f"{peso_kg:.2f} kg", inline=True)
                embed.add_field(name="Height", value=f"{altezza_m:.2f} m", inline=True)
                embed.add_field(name="Region", value=regione_pokemon, inline=True)

                # Aggiungi il colore del tipo al messaggio
                for tipo_info in dati_pokemon['types']:
                    if isinstance(tipo_info, dict):
                        tipo = tipo_info['type']['name'].lower()
                        colore = colore_per_tipo(tipo)
                        embed.color = colore
                        break

                # Aggiungi le mosse del Pokémon all'embed
                mosse_url = f"https://pokemondb.net/pokedex/{nome_pokemon.lower()}#dex-moves"
                embed.add_field(name="Moves", value=f"[{nome_pokemon}'s Move List]({mosse_url})", inline=False)

                # Invia il messaggio solo se l'interazione non è già stata risolta
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed)
                await interaction.edit_original_response(embed=embed)

                successo = True

    except Exception as e:
        print(f"Unknown error during command execution: {e}")
        
        # Aggiungi un messaggio di errore all'utente
        await interaction.response.send_message("Ops! There was an error elaborating your request.")

        # Alza nuovamente l'eccezione per il log e la gestione dell'errore
        raise

    finally:
        if successo:
            # Rispondi con "ha finito di lavorare" se tutto è andato bene
            await interaction.edit_original_response(content="Here's the data you were looking for.")
        else:
            # Rispondi con "Il comando non è andato a buon fine." in caso di errore
            await interaction.edit_original_response(content="Your request encountered some issue. Wait some time and retry.")

@bot.tree.command(name="helparceus", description="Shows informations about this bot usage.")
async def helparceus(interaction: discord.Interaction):   
    await interaction.response.send_message("Thank you for using ArceusInfo! This bot is based upon PokèAPI database. If any pokèmon is missing from this list, it's their fault! (Im joking. I love you guys. Your API is fantastic. I just don't know how to code properly.)\nIts usage is pretty simple: /infopokemon [pokemon-name] will give you all the info you might need on your pokèmon adventures.\nBeware: Some pokèmon names have special formats, such as Zygarde, all megas and gigamax have different name formats (For example, MegaRayquaza is listed as rayquaza-mega, and so on). Since i'm too lazy to catch each exception, feel free to use the wiki (lol).\nEnjoy!")

# Run the bot / Avvio del bot
with open(r'your-config-file-directory/config.json', 'r') as file:
    data = json.load(file)

client.run(data['token'])
