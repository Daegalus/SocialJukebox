import json
from threading import Timer, Event
from flask import Flask, request
from lxml import html
from pytube import YouTube
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String
import soundcloud
from mpd import MPDClient

Base = declarative_base()
yt = YouTube()
engine = create_engine('sqlite:///sj.db', echo=True)
Session = sessionmaker(bind=engine)

started = False
app = Flask(__name__)

media_player = MPDClient()
media_player.connect('localhost', 6600)
media_player.consume(1)
media_player.single(1)


class SongPlayer():

    def __init__(self, session, media_player, event):
        self.Session = session
        self.media_player = media_player
        self.playing = False
        self.current_url = None
        self.current_title = None
        self.current_ourl = None
        self.event = event

    def run(self):
        self.next_song()
        RepeatingTimer(2, self.wait_till_stopped)

    def end_callback(self):
        self.playing = False
        self.next_song()

    def play_song(self, url):
        self.playing = True
        self.media_player.clear()
        self.media_player.add(url)
        self.media_player.play()

    def wait_till_stopped(self):
        if self.media_player.status()['state'] == "stop" and self.playing:
            self.end_callback()

    def next_song(self):
        if not self.playing:
            session = self.Session()
            count = session.query(Song).order_by(Song.sid).count()
            if count > 0:
                row = session.query(Song).order_by(Song.sid)[0]
                session.delete(row)
                self.current_title = row.title
                self.current_url = row.url
                self.current_ourl = row.ourl
                session.commit()
                self.play_song(row.url)


class Song(Base):
    __tablename__ = 'songs'

    sid = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    ourl = Column(String)

    def __init__(self, title, url, ourl):
        self.title = title
        self.url = url
        self.ourl = ourl

    def __repr__(self):
        return '<Song(\'%s\',\'%s\', \'%s\')>' % (self.title, self.url, self.ourl)


class RepeatingTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        super(RepeatingTimer, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.function = function
        self.interval = interval
        self.start()

    def start(self):
        self.callback()

    def stop(self):
        self.interval = False

    def callback(self):
        if self.interval:
            self.function(*self.args, **self.kwargs)
            Timer(self.interval, self.callback, ).start()


@app.route('/', methods=['GET'])
def index():
    indexhtml = open('static/index.html', 'r')
    return ''.join(indexhtml.readlines())


@app.route('/add', methods=['GET'])
def add_song():
    url = request.args.get('url')
    process_song(url)
    return ''


@app.route('/getsongs', methods=['GET'])
def get_songs():
    session = Session()
    rows = session.query(Song).order_by(Song.sid)
    output = []
    for row in rows:
        song = {'sid': row.sid, 'url': row.url, 'title': row.title}
        output.append(song)
    out = {'success': True, 'songs':  output}
    print(out)
    return json.dumps(out)


@app.route('/getcurrent', methods=['GET'])
def get_current_song():
    url = song_player.current_url
    ourl = song_player.current_ourl
    title = song_player.current_title
    if url is None:
        return ''
    out = {'success': True, 'url': url, 'title': title, 'ourl': ourl}
    return json.dumps(out)


@app.route('/jukebox/stop', methods=['GET'])
def stop():
    media_player.stop()
    song_player.current_ourl = None
    song_player.current_url = None
    song_player.current_title = None
    return ''

@app.route('/jukebox/pause', methods=['GET'])
def pause():
    media_player.pause(1)
    return ''


@app.route('/jukebox/start', methods=['GET'])
def start():
    song_player.next_song()
    return ''


@app.route('/jukebox/resume', methods=['GET'])
def resume():
    media_player.pause(0)
    return ''

@app.route('/jukebox/s/<sid>', methods=['DELETE'])
def delete(sid):
    session = Session()
    song = session.query(Song).get(sid)
    session.delete(song)
    session.commit()
    return ''


def process_song(url):
    if 'soundcloud' in url:
        add_soundcloud(url)
    elif 'youtube' in url:
        add_youtube(url)
    elif '.mp3' or '.aac' or '.flv' in url:
        add_raw_song(url)
    else:
        add_unknown_format(url)
    song_player.next_song()


def add_soundcloud(track_url):
    client = soundcloud.Client(client_id='3*2')
    resolved = client.get('/resolve', url=track_url)
    track_get = '/tracks/%d' % resolved.id
    track = client.get(track_get)
    stream_url = client.get(track.stream_url, allow_redirects=False)
    song = Song(track.title, stream_url.location.replace('https', 'http'), track_url)
    session = Session()
    session.add(song)
    session.commit()


def add_youtube(url):
    title = html.parse(url).xpath('//title')[0].text_content().replace(' - YouTube', '')
    yt.url = url
    video = yt.videos[-1]
    vurl = video.url
    add_raw_song(title, vurl, url)


def add_unknown_format(url):
    add_raw_song(url, url, '')


def add_raw_song(title, url, ourl):
    song = Song(title, url, ourl)
    session = Session()
    session.add(song)
    session.commit()


def init_db():
    #Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    init_db()
    global event
    event = Event()
    event.set()
    global song_player
    song_player = SongPlayer(Session, media_player, event)
    song_player.run()
    app.run(debug=True, use_reloader=False)


__author__ = 'Yulian Kuncheff'
