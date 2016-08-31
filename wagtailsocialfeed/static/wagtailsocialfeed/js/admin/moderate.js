$(document).ready(function() {
    $('table#feeds tbody').on('click', 'td.status .status-actions a', function(e) {
        e.preventDefault();
        var url = $( this ).attr('href');

        var postId = $( this ).data('post_id');
        var originalpost = $( 'input#post_original_' + postId ).val();
        var $td = $( this ).parents('td.status');

        var postdata = {
            'original': originalpost
        };

        $.post(url, postdata, function(data) {
            $td.addClass('new-state');
            if (data.allowed) {
                $td.addClass('allowed');
            }
            else {
                $td.removeClass('allowed');
            }
        })
    });

    $('table#feeds tbody').on('mouseleave', 'td.status.new-state', function(e) {
        $( this ).removeClass('new-state');
    });
})
