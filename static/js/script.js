var timeout = 1000;
var timer = '';

$(function() {
  var gId = '';
  var cId = '';

  // Create Game
  $('#createGame').click(function() {
    $('#message').empty();
    $.ajax('create' + '/' + $('#cName_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#gId').text(data);
      $('#cId').text(data);
      $('#cName').text($('#cName_inp').val());
      $('#gStatus').text('waiting');
      gId = data;
      cId = data;
      $('#sec1').show();
      timer = setTimeout(status_check(gId, cId), timeout)
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Join Game
  $('#joinGame').click(function() {
    $('#message').empty();
    $.ajax($('#gId_inp').val() + '/join/' + $('#cName_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      _tmp = data.split(' ,');
      $('#cId').text(_tmp[0]);
      $('#cName').text(_tmp[1]);
      $('#gStatus').text(_tmp[2]);
      gId = $('#gId_inp').val();
      cId = _tmp[0];
      timer = setTimeout(status_check(gId, cId), timeout)
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Start Game
  $('#startGame').click(function() {
    $('#message').empty();
    $.getJSON(gId + '/start',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $("#sleep").attr('disabled', false);
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Go to sleep
  $('#sleep').click(function() {
    $('#message').empty();
    // put your card
    $.ajax(gId + '/' + cId + '/sleep',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#message').text(data);
      $("#nextPlayer").attr('disabled', true);
      $("#sleep").attr('disabled', true);
      $('#sec3').show();
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Next player
  $('#nextPlayer').click(function() {
    $('#message').empty();
    $.ajax(gId + '/' + cId + '/next/' + $('input[name="area"]:checked').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      // console.log(data)
      $('#message').text('次の人に移動しました');
      $('#nextPlayer').attr('disabled', true);
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });
});

var status_check = function(gId, cId){
  setTimeout(function(){
    $('#message').empty();
    // all status
    $.getJSON(gId + '/status',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      console.log(data)
      $('#gStatus').text(data.status);
      playerPos = 0;

      // Applying List
      $('#applyingList').empty();
      for(var pIdx in data.players){
        // console.log(data.players[pIdx])
        $('#applyingList').append(data.players[pIdx].nickname + '(' + data.players[pIdx].playerid + ')' + ',');
        if(cId == data.players[pIdx].playerid){
          playerPos = pIdx;
        }
      }

      if(data.status == 'started'){
        $('#sec2').show()
        $('#sec4').hide()
        // route List
        $('#routeList').empty();
        for(var rIdx in data.routelist){
          if(data.routelist[rIdx].playerid == data.routeid){
            $('#routeList').append('<b>&gt;' + data.routelist[rIdx].nickname + '</b><br/>');
          }else{
            $('#routeList').append(data.routelist[rIdx].nickname + '<br/>');
          }
        }

        // game cards
        holdcards = data.players[playerPos].holdcards;
        for(var i = 0; i < 6; i++){
          $('#tdcard'+i).empty();
          if(i < holdcards.length){
            // switch(Math.floor(holdcards[i] / 5)){
            // switch(holdcards[i] % 5){
            //   case 0:
            //     $('#tdcard'+i).css("background-color","#e55050");
            //     break;
            //   case 1:
            //     $('#tdcard'+i).css("background-color","#50b4e5");
            //     break;
            //   case 2:
            //     $('#tdcard'+i).css("background-color","#e5b450");
            //     break;
            //   case 3:
            //     $('#tdcard'+i).css("background-color","#50e550");
            //     break;
            // }
            if(holdcards[i] % 5 == 4){
              // $('#card'+i).text('J');
              // $('#tdcard'+i).css("background-color","#b450e5");
              $('<img width="100" src="static/img/picj.jpg">').appendTo($('#tdcard'+i));
            }else{
              // $('#card'+i).text(Math.floor(holdcards[i] / 5));
              $('<img width="100" src="static/img/pic' + holdcards[i] + '.jpg">').appendTo($('#tdcard'+i));
            }
            $('#rCard'+i).val(holdcards[i]);
            $('#rCard'+i).show();
          }else{
            // $('#card'+i).text('');
            // $('#tdcard'+i).css("background-color","#fff");
            $('#rCard'+i).val('');
            $('#rCard'+i).css('display', 'none');
            $('#tdcard'+i).empty();
          }
        }

        $('#sleptList').text('')
        for(var sIdx in data.slept){
          $('#sleptList').append(data.slept[sIdx].nickname + ',');
        }

        // checking turn
        if(data.routeid == cId){
          $('#nextPlayer').attr('disabled', false)
          $('#sleep').attr('disabled', true)
          if(data.players.length -1 == data.slept.length){
            $("#result_lose").dialog();
          }
        }else{
          $('#nextPlayer').attr('disabled', true)
          if(!data.players[playerPos].status){
            $('#sleep').attr('disabled', false)
          }else{
            $('#sleep').attr('disabled', true)
          }
          if(data.players.length -1 == data.slept.length){
            $("#result_win").dialog();
          }
        }
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
    timer = setTimeout(status_check(gId, cId), timeout)
  }, timeout);
}
