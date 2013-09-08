setInterval(getSongs, 5000);

function getSongs() {
    $.ajax({
        url: '/getsongs',
        method: 'GET'
    }).done(function(data) {
        if (data) {
            var json = JSON.parse(data);
            var songs = json.songs;
            $('.song-list').empty();
            if (songs) {
                for (var i = 0; i < songs.length; i++) {
                    addSong(songs[i]);
                }
            }
        }
        $.ajax({
            url: '/getcurrent',
            method: 'GET'
        }).done(function(data) {
            $('.current-list').empty();
            if (data) {
                var json = JSON.parse(data);
                addCurrentSong(json);
            }
        });
    });
}

function addSong(song) {
    var asong = $('<a/>');
    asong.attr('href', song.ourl);
    asong.append(song.title);

    var tdsong = $('<td/>');
    tdsong.addClass('col-xs-11');
    tdsong.append(asong);

    var removeicon = $('<span/>');
    removeicon.addClass('glyphicon').addClass('glyphicon-remove');

    var aremove = $('<a/>');
    aremove.addClass('sj-remove').attr('sid', song.sid).attr('href', '#');
    aremove.click(function () {
        var sid = $(this).attr('sid');
        $.ajax({
            url: '/jukebox/s/' + sid,
            method: 'DELETE'
        })
        .done(function() {
            $('tr[song-entry='+sid+']').remove()
        });
    });
    aremove.append(removeicon);

    var tdremove = $('<td/>');
    tdremove.addClass('col-xs-1');
    tdremove.append(aremove);

    var tr = $('<tr/>');
    tr.attr('song-entry', song.sid);
    tr.append(tdsong).append(tdremove);

    $('.song-list').append(tr);
}

function addCurrentSong(song) {
    var asong = $('<a/>');
    asong.attr('href', song.ourl);
    asong.append(song.title);

    var tdsong = $('<td/>');
    tdsong.addClass('col-xs-11');
    tdsong.append(asong);

    var playicon = $('<span/>');
    playicon.addClass('glyphicon').addClass('glyphicon-play');

    var pauseicon = $('<span/>');
    pauseicon.addClass('glyphicon').addClass('glyphicon-pause');

    var stopicon = $('<span/>');
    stopicon.addClass('glyphicon').addClass('glyphicon-stop');

    var aplay = $('<a/>');
    aplay.addClass('sj-play').attr('href', '#');
    aplay.click(function () {
        $.ajax({
            url: '/jukebox/resume',
            method: 'GET'
        })
        .done(function() {
            $('.currently-playing').removeClass('warning').addClass('success');
        });
    });
    aplay.append(playicon);

    var apause = $('<a/>');
    apause.addClass('sj-pause').attr('href', '#');
    apause.click(function () {
        $.ajax({
            url: '/jukebox/pause',
            method: 'GET'
        })
        .done(function() {
            $('.currently-playing').removeClass('success').addClass('warning');
        });
    });
    apause.append(pauseicon);

    var astop = $('<a/>');
    astop.addClass('sj-stop').attr('href', '#');
    astop.click(function () {
        $.ajax({
            url: '/jukebox/stop',
            method: 'GET'
        })
        .done(function() {
            $('.current-list').empty();
        });
    });
    astop.append(stopicon);

    var tdcontrols = $('<td/>');
    tdcontrols.addClass('col-xs-1');
    tdcontrols.append(aplay);
    tdcontrols.append(apause);
    tdcontrols.append(astop);

    var tr = $('<tr/>');
    tr.addClass("success").addClass('currently-playing');
    tr.append(tdsong).append(tdcontrols);

    $('.current-list').append(tr);
}

    function uploadSong(url) {
        $.ajax({
            url: '/add',
            method: 'GET',
            data: {'url': url}
        }).done(function() {
            getSongs();
        });
    }

    $('#addsong').click(function() {
        uploadSong($('#songurl').val());
    });

