"""
Bot discord.
Permet de générer des phrases à partir des phrases d'un utilisateur discord.
Utilise CreateSentence pour la génération de phrase.

Il est aussi possible d'utiliser ce bot pour sauvegarder
les phrases dans un fichier csv.
"""
import os
import time
import math
import typing

import discord
from discord.ext.commands import Cog, Bot, Context, command
from discord import Member

import pandas as pd
import numpy as np
from PIL import Image

import torchvision

from src.create_sentence import CreateSentence
from src.VAE import config, model_name, load_model


class AzuriaBot(Cog):
    """
    Le meilleur bot fait de cristal et d'azur.

    Version: v1.2
    """
    def __init__(self, bot: Bot, build_database: bool=False,
            author: str='AzuriaCristal', n: int=3):
        self.bot = bot
        self.author = author
        self.build_database = build_database

        self.df = pd.read_csv(os.getenv('DATABASE'))
        content = self.df[ self.df['author'] == author ]['content']
        self.create_sentence = CreateSentence(content.dropna(), n)

        # Réponse automatique - paramètres
        self.last_send = time.time()
        self.scale = 18  # 18 heures d'attente en moyenne
        self.delta_min = np.random.exponential(self.scale)
        self.last_send_azuria = time.time()
        self.scale_azuria = 2
        self.delta_min_azuria = np.random.exponential(self.scale_azuria)

        # Chargement du modèle PyTorch
        self.vae = load_model(config, model_name)

    @Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            print(f'Connected to {guild.name}')

            if not self.build_database:
                continue

            data = {
                'message_id': [],
                'author': [],
                'author_id': [],
                'content': [],
                'channel_name': [],
                'date': [],
            }

            for channel in guild.text_channels:
                limite = None
                i = 0
                print(channel.name)
                async for message in channel.history(limit=limite):
                    data['message_id'].append(message.id)
                    data['author'].append(message.author.name)
                    data['author_id'].append(message.author.id)
                    data['content'].append(message.content)
                    data['date'].append(message.created_at)
                    data['channel_name'].append(channel.name)

                    i += 1
                    if i % 1000 == 0:
                        print(i)

            df = pd.DataFrame(data)
            filename = guild.name.replace(' ', '_') + '.csv'
            df.to_csv(filename, index=False)

    @Cog.listener()
    async def on_message(self, context: Context):
        """
        Réponds de temps en temps aux messages.
        Pour savoir si on a le droit de répondre, on utilise
        une variable aléatoire 'next_send', qui suit une loi exponentielle.

        Réponds à AzuriaCristal avec une dynamique personnalisée.
        """
        if context.content.startswith('!'):
            return  # Ne fait rien

        if context.author.name == 'AzuriaCristal':
            delta_time = time.time() - self.last_send_azuria
            if delta_time > self.delta_min_azuria * 60 * 60:
                self.delta_min_azuria = np.random.exponential(self.scale_azuria)
                self.last_send_azuria = time.time()
                await context.channel.send(self.create_sentence.sentence())
            return

        delta_time = time.time() - self.last_send
        if delta_time > self.delta_min * 60 * 60:
            self.delta_min = np.random.exponential(self.scale)
            self.last_send = time.time()
            await context.channel.send(self.create_sentence.sentence())


    @command(name='regalemoi')
    async def azuregale(self, context: Context):
        """
        ;)
        """
        await context.send(self.create_sentence.sentence())

    @command(name='depth')
    async def azurdepth(self, context: Context, depth: typing.Optional[int]):
        """
        Change la profondeur de la chaîne de Markov.
        Une grande profondeur augmente la cohérence des phrases,
        mais diminue son originalité.

        Affiche la profondeur actuelle si appelé sans argument.
        """
        if depth:
            content = self.df[ self.df['author'] == self.author ]['content']
            self.create_sentence = CreateSentence(content.dropna(), depth)

        await context.send(f'Profondeur actuelle: {self.create_sentence.n}')

    @command(name='person')
    async def azurauthor(self, context: Context, author: typing.Optional[str]):
        """
        Change la personnalité du bot.

        Il faut donner le nom du compte discord.
        Si ce nom n'est pas connu, la commande ne fonctionnera pas.

        Affiche la liste des noms valides si appelé sans argument.
        """
        counts = self.df.groupby('author').count()
        counts = counts[ counts['content'] > 500 ]
        valid_users = sorted(counts.index)

        if author:
            if author in valid_users:
                self.author = author
                content = self.df[ self.df['author'] == self.author ]['content']
                self.create_sentence = CreateSentence(content.dropna(), self.create_sentence.n)

                await context.send(f'Je suis maintenant le double de {self.author}')
                return

            await context.send('Utilisateur non valide')

        list_users = f'Je suis actuellement {self.author}\n\n'
        list_users += 'Liste des utilisateurs valides:\n'
        for u in valid_users:
            list_users += f' - {u}\t{counts.loc[u, "content"]}\n'

        await context.send(list_users)

    @command(name='kawai')
    async def azurkawai(self, context: Context, number: typing.Optional[int]=1):
        """
        Génère une tête.
        """
        if number > 100 or number < 1:
            await context.send('Tu forces gros')

        image = self.vae.generate(number)
        nrow = best_nrow(number)

        image = torchvision.utils.make_grid(image, nrow=nrow)
        image = image.permute(1, 2, 0)  # [width, height, RGB]
        image = image.numpy()
        image = np.uint8(image * 255)
        image = Image.fromarray(image)

        image.save('anime.png')

        await context.send(file=discord.File('anime.png'))

def best_nrow(n):
    nrow = int(math.sqrt(n))
    while n % nrow != 0:
        nrow += 1
    return nrow
