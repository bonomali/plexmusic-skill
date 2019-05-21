import os
import sys
import time
from collections import defaultdict

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_file_handler, intent_handler
from mycroft.util.log import LOG
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from mycroft.util.parse import match_one
from json import load, dump
import vlc

__author__ = 'colla69'


def refresh_library(path):
    pass


class PlexMusicSkill(CommonPlaySkill):

    def CPS_match_query_phrase(self, phrase):
        title, t_prob = self.title_search(phrase)
        artist, a_prob = self.artist_search(phrase)
        album, al_prob = self.album_search(phrase)
        print("""
        %s %f
        %s %d
        %s %d        
        """ % (title, t_prob, artist, a_prob, album, al_prob))

        if t_prob > al_prob and t_prob > a_prob:
            data = {
                "title": title,
                "file": self.titles[title]
            }
            return phrase, CPSMatchLevel.TITLE, data
        elif a_prob >= al_prob:
            data = {
                "title": artist,
                "file": self.artists[artist]
            }
            return phrase, CPSMatchLevel.MULTI_KEY, data
        elif al_prob > a_prob:
            data = {
                "title": album,
                "file": self.albums[album]
            }
            return phrase, CPSMatchLevel.MULTI_KEY, data
        else:
            return None

    def CPS_start(self, phrase, data):
        if self.get_running():
            self.player.stop()
        title = data["title"]
        link = data["file"]
        try:
            m = self.vlcI.media_list_new(link)
            self.player.set_media_list(m)
            self.player.play()
        except Exception as e:
            print(type(e))
            print("Unexpected error:", sys.exc_info()[0])
            raise
        finally:
            time.sleep(2)
            if not self.get_running():
                self.speak("playback problem")

    def __init__(self):
        super().__init__(name="TemplateSkill")
        self.music_source = self.settings.get("musicsource", "")
        self.artists = defaultdict(list)
        self.albums = defaultdict(list)
        self.titles = defaultdict(list)
        self.vlcI = vlc.Instance()
        self.player = self.vlcI.media_list_player_new()
        self.get_play_status()

    def get_play_status(self):
        self.play_status = self.player.is_playing()

    def get_running(self):
        self.get_play_status()
        return self.play_status

    def load_data(self):
        datapath = os.path.expanduser(self.music_source.strip() + "data.json")
        LOG.info("loading "+datapath)
        if os.path.isfile(datapath):
            data = self.json_load(datapath)
        else:
            """ dialog uh I don't seem to know your library yet """
            """ dialog let me load that for you, """
            """ dialog this could take some time """
            LOG.info("making new JsonData ")
            #f_count, data, errors = self.get_data_from_dir()
            #print("loaded " + str(f_count) + " files , with " + str(errors) + " errors")
            #self.json_save(data, self.rootDir+"data.json")
            """ dialog we are ready to go """

        for artist in data:
            for album in data[artist]:
                for song in data[artist][album]:
                    title = song[0]
                    file = song[1]
                    self.albums[album].append(file)
                    self.artists[artist].append(file)
                    self.titles[title].append(file)

    def initialize(self):
        self.load_data()

    def json_save(self, data, fname):
        with open(fname, 'w') as fp:
            dump(data, fp)

    def json_load(self, fname):
        with open(fname, 'r') as fp:
            return load(fp)

    def title_search(self, phrase):
        probabilities = process.extractOne(phrase, self.titles.keys(), scorer=fuzz.ratio)
        artist = probabilities[0]
        confidence = probabilities[1]
        return artist, confidence

    def artist_search(self, phrase):
        probabilities = process.extractOne(phrase, self.artists.keys(), scorer=fuzz.ratio)
        artist = probabilities[0]
        confidence = probabilities[1]
        return artist, confidence

    def album_search(self, phrase):
        probabilities = process.extractOne(phrase, self.albums.keys(), scorer=fuzz.ratio)
        album = probabilities[0]
        confidence = probabilities[1]
        return album, confidence

    @intent_file_handler('play.music.intent')
    def handle_play_music_intent(self, message):
        pass

    @intent_file_handler('pause.music.intent')
    def handle_pause_music_intent(self, message):
        self.player.pause()

    @intent_file_handler('next.music.intent')
    def handle_next_music_intent(self, message):
        self.player.next()

    @intent_file_handler('reload.library.intent')
    def handle_reload_library_intent(self, message):
        self.speak_dialog("refresh.library")
        self.load_data()

    def converse(self, utterances, lang="en-us"):
        return False

    def stop(self):
        self.player.stop()
        self.vlcI.release()


def create_skill():
    return PlexMusicSkill()
