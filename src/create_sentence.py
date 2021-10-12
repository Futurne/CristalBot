"""
Read the content of each tweets, and manage to create a new tweet
according to the frequence of each words in the text.
For each words, we know what are the next possible words and their frequencies.
"""
from collections import defaultdict
from random import random

class WordLink:
    """
    Data structure to remember what word can follow the
    particular word given.
    """
    def __init__(self, word):
        self.word = word # The given word
        self.link = defaultdict(int) # Key is a following word, value is how many times it happened
        self.start_count = 0 # Does that word can start a sentence ?
        self.end_count = 0 # Does that word can end a sentence ?
        self.sum_possibilities = 0 # How much words / ends there have been after this word ?

    def add_link(self, word):
        self.link[word] += 1
        self.sum_possibilities += 1

    def incr_start(self):
        self.start_count += 1

    def incr_end(self):
        self.end_count += 1
        self.sum_possibilities += 1

    def __repr__(self):
        return "{}:\n{} starts\n{} ends\n{} next_possibilities".format(
                self.word, self.start_count, self.end_count, self.sum_possibilities)


class CreateSentence:
    """
    Manipulates WordLink to create a sentence.
    """
    def __init__(self, content, n=3):
        self.link_words = dict()
        self.sum_starts = 0 # How much differents starts there are ?
        self.n = n

        content = CreateSentence.preprocess_content(content)
        self._init_probabilities(content)

    def _init_probabilities(self, content):
        n = self.n
        for cont in content:
            words = cont.split(' ')
            words = [w.lower() for w in words]

            # Start prob
            self.add_start(words[0])

            # Middle prob
            for i, w in enumerate(words[1:]):
                i += 1
                for j in range(max(i-n, 0), i):
                    p = words[j:i]
                    p = ' '.join(p)
                    self.add_link(p, w)

            # End prob
            for j in range(max(len(words)-n, 0), len(words)):
                p = words[j:len(words)]
                p = ' '.join(p)
                self.add_end(p)

        # Remove the high prob with punctuations
        punc = set('?!.')
        for p in punc:
            for i in range(1, self.n + 1):
                word = ' '.join([p for _ in range(i)])
                if word not in self.link_words:
                    continue

                word_link = self.link_words[word]

                p_score = word_link.link[p]
                others = word_link.sum_possibilities - p_score
                word_link.link[p] = others / 4

        # Make starting words more probable if they
        # have a better chance to lead to a longer sentence
        for word_link in self.link_words.values():
            if word_link.end_count / word_link.sum_possibilities > 0.5:
                # Lower chance of ending sentence
                others = word_link.sum_possibilities - word_link.end_count
                word_link.end_count = others / 2
                word_link.sum_possibilities = others + word_link.end_count

                # Lower chance of starting with that word
                remove_count = word_link.start_count / 2
                word_link.start_count -= remove_count
                self.sum_starts -= remove_count

    def add_link(self, previous_word, next_word):
        self.add_word(previous_word)
        self.link_words[previous_word].add_link(next_word)

    def add_start(self, starting_word):
        self.add_word(starting_word)
        self.link_words[starting_word].incr_start()
        self.sum_starts += 1

    def add_end(self, ending_word):
        self.add_word(ending_word)
        self.link_words[ending_word].incr_end()

    def add_word(self, word):
        if word not in self.link_words:
            self.link_words[word] = WordLink(word)

    def choose_start(self):
        r = random()
        tot = 0
        for word_link in self.link_words.values():
            tot += word_link.start_count / self.sum_starts
            if tot >= r:
                return word_link.word

        return None # Error

    def choose_next(self, previous_words):
        if previous_words not in self.link_words:
            return None  # Previous words not found

        r = random()
        tot = 0
        word_link = self.link_words[previous_words]
        for next_word, count in word_link.link.items():
            tot += count / word_link.sum_possibilities
            if tot >= r:
                return next_word

        return '[END]' # End the sentence

    def sentence(self, max_words=100):
        sentence = [self.choose_start()]
        next_word = self.choose_next(sentence[0])
        while next_word != '[END]' and len(sentence) < max_words:
            sentence.append(next_word)

            start_idx = max(len(sentence) - self.n, 0)
            next_words = []
            for j in range(start_idx, len(sentence)):
                p = sentence[j:len(sentence)]
                p = ' '.join(p)
                next_words.append(self.choose_next(p))

            next_word = '[END]'
            for w in reversed(next_words):
                if w is not None and w != '[END]':
                    next_word = w

        sentence = ' '.join(sentence)
        return CreateSentence.process_sentence(sentence)

    def process_sentence(sentence):
        """
        Do some transformations to make the sentence
        more readable.

        word1 ' word2 => word1'word2
        word1 , word2 => word1, word2
        word1 . => word1.
        """
        sentence = sentence.replace(' ,', ',')
        sentence = sentence.replace(" ' ", "'")

        punc = set('?!.')
        for p in punc:
            sentence = sentence.replace(f' {p}', p)

        return sentence

    def preprocess_content(content):
        """
        Preprocess phrases.

        List of tasks:
         - lowerise
         - punctuation
         - remove youtube links
        """
        punc = set(',.\'"!?')
        to_remove = set('"«»«»')
        preprocessed = []
        for cont in content:
            if cont.startswith(';;') or cont.startswith('!'):
                continue  # Pass

            if cont.startswith('http'):
                if 'youtu.be' in cont:
                    continue  # Mostly dead link

                preprocessed.append(cont)
                continue  # Save content and then pass

            cont = cont.replace('’', "'")
            for p in punc:
                cont = cont.replace(p, f' {p} ')

            words = cont.split(' ')
            words = [w.lower() for w in words
                     if w != '']
            words = [w for w in words
                     if w not in to_remove]

            cont = ' '.join(words)
            cont = cont.replace('<@ ! ', '<@!')
            preprocessed.append(cont)

        return preprocessed
