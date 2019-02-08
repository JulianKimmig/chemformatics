
$('#myTab a').first().tab('show');
$('#myTab a[href="'+window.location.hash+'"]').tab('show');

$('#myTab a').click(function (e) {
    $(this).tab('show');
    var scrollmem = $('body').scrollTop() || $('html').scrollTop();
    window.location.hash = this.hash;
    $('html,body').scrollTop(scrollmem);
});
var progressb =$( "#progressbar" );
progressb.progressbar({
    value: 100
});
$(function () {
    $.ajaxSetup({
        headers: { "X-CSRFToken": $('meta[name="csrf-token"]').attr('content')}
    });
});

function upload_file(form,url) {
    $.ajax({
        url: url,
        type: 'POST',

        data: new FormData(form),
        cache: false,
        contentType: false,
        processData: false,
        // Custom XMLHttpRequest
        xhr: function() {
            var myXhr = $.ajaxSettings.xhr();
            if (myXhr.upload) {
                // For handling the progress of the upload
                myXhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        progressb.progressbar( "value", e.total*100/e.loaded )
                    }
                } , false);
            }
            return myXhr;
        }
    });
}

function upload_raw(){
    var rdf = $('#raw_data_form');
    if(rdf.find('[name="raw_data"]').val() !== '') {
        $("<div title='upload raw'>Uploading raw data will delete old data (<a href='" + raw_data_link + "' download>download</a>)</div>").dialog({
            resizable: false,
            height: "auto",
            width: 400,
            modal: true,
            buttons: {
                "Upload": function () {
                    $(this).dialog("close");
                    upload_file(rdf.get(0), raw_data_post);
                },
                Cancel: function () {
                    $(this).dialog("close");
                }
            }
        });
    }
    //a = confirm("");
}


function connect() {
    var ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    var ws =  new WebSocket(ws_scheme + '://' + window.location.host + "/ws" );//window.location.pathname
    ws.onopen = function() {
        // subscribe to some channels
       // ws.send(JSON.stringify({
            //.... some message the I must send when I connect ....
       // }));
    };

    ws.onmessage = function(e) {
        console.log('Message:', e.data);
    };

    ws.onclose = function(e) {
        console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
        setTimeout(function() {
            connect();
        }, 1000);
    };

    ws.onerror = function(err) {
        console.error('Socket encountered error: ', err.message, 'Closing socket');
        ws.close();
    };
}

connect();