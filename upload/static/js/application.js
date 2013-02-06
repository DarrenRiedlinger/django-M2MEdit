// TODO: programatically incorporate options (i.e maxfilesize) via cookies?
/*
 * jQuery File Upload Plugin JS Example 5.0.2
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://creativecommons.org/licenses/MIT/
 */

/*jslint nomen: true */
/*global $ */

$(function() {
	'use strict';
	// Replace non-js link with the multifile upload form
	$('#upload_link').replaceWith($('#fileupload'))
	$('#fileupload').show()

	// initialize the jquery file upload widget
	// for a complete option reference go to
	// https://github.com/blueimp/jquery-file-upload
	$('#fileupload').fileupload({
		// this formdata is neccessary to pass the csrf and pass uid to django
		formdata: [
	{ name: "csrfmiddlewaretoken", value: $('input[name=csrfmiddlewaretoken]').val() },
		],
	//	maxFileSize: {{ maxfilesize }},
	//	minFileSize: {{ minfilesize }},
		sequentialUploads: true
	});

	// Load existing files
	$.getJSON($('#fileupload form').prop('action'), function (files) {
		var fu = $('#fileupload').data('fileupload');
		fu._adjustMaxNumberOfFiles(-files.length);
		fu._renderDownload(files)
		.appendTo($('#fileupload .files'))
		.fadeIn(function () {
			// Fix for IE7 and lower:
			$(this).show();
		});
	});
	
	// open download dialogs via iframes,
	// to prevent aborting current uploads
	$('#fileupload .files a:not([target^=_blank])').live('click', function (e) {
		e.preventDefault();
		$('<iframe style="display:none;"></iframe>')
		.prop('src', this.href)
		.appendTo('body');
	});
});
