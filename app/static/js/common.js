$(document).ready(function(){

    // Ez ajax marking of beef resolved
    $('td a.logs-mark-resolved').click(function(e){
        e.preventDefault();
        var $this = $(this);

        // Set to loading state
        $this.button('loading');

        // Send request
        $.ajax({
            content: this,
            type: 'GET',
            url: this.href,
            dataType: 'json',
            success: function(data) {
                // If successful, delete row.
                if (data.success == true)
                {
                    $this.closest('td').text("Resolved.");
                    $this.remove();
                }
            }
        });
    });
});
