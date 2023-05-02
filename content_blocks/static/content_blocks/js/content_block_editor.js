(function ($) {
  $.fn.ContentBlockEditor = function (options) {
    let settings = $.extend({}, options);

    const delete_active_class = 'fa-trash';
    const delete_disabled_class = 'fa-trash-slash';

    $(document).ajaxError(function (e, j, s, thrownError) {
      showStatus('Something went wrong. Please reload the page and try again.');
      console.log(thrownError);
    });

    // Initialise dragon drops.
    $('.content-blocks').each(function () {
      dragonDrop($(this));
    });

    // Import button and select
    let $cb_import_select = $('#id_master');
    let $cb_import_label = $('#cb_import_label');
    updateButtonLabel($cb_import_select, $cb_import_label);

    $(document).on('change', '#id_master', function () {
      updateButtonLabel($cb_import_select, $cb_import_label);
    });

    $(document).on('submit', '.import-form', function () {
      let $form = $(this);
      let $target = $('#content-blocks-root');
      let $loader = $($(this).data('loader'));

      showLoader($loader);

      let title = $form.find('#cb_import_label').html();
      showStatus('Importing content blocks from ' + title);
      $form.ajaxSubmit({
        success: function (data) {
          renderAjaxResponse(data, $target, true);
          hideLoader($loader);
          showStatus('Content blocks imported from ' + title);
        },
      });

      return false;
    });

    // Create button and select
    let $cb_template_select = $('#new_cb_content_block_template');
    let $cb_create_button_label = $('#cb_create_label');
    updateButtonLabel($cb_template_select, $cb_create_button_label);

    $(document).on('change', '#new_cb_content_block_template', function () {
      updateButtonLabel($cb_template_select, $cb_create_button_label);
    });

    $(document).on('submit', '.create-form', function () {
      let $form = $(this);
      let $target = $('#content-blocks-root');
      let $position = $form.find('#new_cb_position');

      $position.val($target.children('.content-block-form').length);

      let title = $form.find('#cb_create_label').html();
      showStatus('Creating ' + title);

      $form.ajaxSubmit({
        success: function (data) {
          renderAjaxResponse(data, $target, true);
          showStatus(title + ' created');
        },
      });

      return false;
    });

    // Create nested buttons and select
    $('.nested-create-form').each(function () {
      updateButtonLabel(
        $(this).children('select'),
        $(this).find('.nested-create-label'),
      );
    });

    $(document).on('change', '.nested-create-form select', function () {
      updateButtonLabel($(this), $(this).parent().find('.nested-create-label'));
    });

    $(document).on('submit', '.nested-create-form', function () {
      let $form = $(this);

      if ($form.hasClass('disabled')) {
        return false;
      }

      let $target = $($form.data('target'));
      let $position = $form.find('input[name="position"]');

      $position.val($target.children('.content-block-form').length);

      let title = $form.find('.nested-create-label').html();
      showStatus('Creating ' + title);

      $form.ajaxSubmit({
        success: function (data) {
          renderAjaxResponse(data, $target, true);
          enforceLimits($target);
          showStatus(title + ' created');
        },
      });
      return false;
    });

    // Content block save button
    $(document).on('click', 'button.save', function () {
      let $btn = $(this);
      saveContentBlock($btn);
    });

    // Toggle visible button
    $(document).on('click', 'button.visible', function () {
      let $btn = $(this);
      let ajax_url = $btn.data('ajax_url');
      let label = $($btn.data('label')).text();

      $.ajax({
        type: 'POST',
        url: ajax_url,
        success: function (data) {
          let $icon = $btn.children('i');
          $icon.removeClass('fa-eye fa-eye-slash');
          if (data.visible) {
            $icon.addClass('fa-eye');
            showStatus(label + ' shown');
          } else {
            $icon.addClass('fa-eye-slash');
            showStatus(label + 'hidden');
          }
        },
      });
    });

    // Preview button
    $(document).on('click', 'button.preview', function (e) {
      let $btn = $(this);
      let $target = $($btn.data('target'));

      if ($target.hasClass('open')) {
        $target.slideUp().removeClass('open');
      } else {
        saveForPreview($btn, function () {
          loadPreview($btn);
        });
      }
    });

    // Delete button
    $(document).on('click', 'button.delete', function () {
      let $btn = $(this);
      if ($btn.children('i').hasClass(delete_disabled_class)) {
        return false;
      }

      let $target = $($btn.data('target'));
      let $loader = $($btn.data('loader'));
      let ajax_url = $btn.data('ajax_url');

      let $popup_content = $($('#delete_popup_content').html());
      let label = $($btn.data('label')).text();
      $popup_content.find('.label').text(label);

      showPopup($btn, {
        css_class: 'small',
        content: $popup_content,
        confirm_callback: function ($popup) {
          showLoader($loader);
          showStatus('Deleting ' + label);
          $.ajax({
            url: ajax_url,
            type: 'POST',
            dataType: 'json',
            success: function (data) {
              if (data.error) {
                console.log(data.error);
              } else {
                let $wrapper = $target.closest('.content-blocks');
                $target.remove();

                $('.content-blocks').sortable('refresh');
                let positions = $wrapper.sortable('serialize');
                ajaxDragonDrop(positions);
                refreshDragonDrop();

                enforceLimits($wrapper);
                toggleImportForm();
                showStatus(label + ' deleted');
              }
            },
          });
        },
      });
    });

    const expand_open_class = 'fa-chevron-up';
    const expand_closed_class = 'fa-chevron-down';

    // Expander button
    $(document).on('click', 'button.expand', function () {
      let $button = $(this);
      let $icon = $button.children('i');
      let $expanders = $($button.data('target'));
      let $wrapper = $button.closest('.ui-sortable');

      $wrapper.css('overflow', 'hidden');

      if ($icon.hasClass(expand_open_class)) {
        $icon.removeClass(expand_open_class).addClass(expand_closed_class);
        $expanders.slideUp(function () {
          $wrapper.css('overflow', 'auto');
        });
      } else {
        $icon.removeClass(expand_closed_class).addClass(expand_open_class);
        $expanders.slideDown(function () {
          $wrapper.css('overflow', 'auto');
        });
      }
    });

    // Collapse all button
    $(document).on('click', '.collapse-all', function () {
      let $target = $($(this).data('target'));
      $target.css('overflow', 'hidden');
      $target
        .children('.content-block-form')
        .children('.pos-rel')
        .children('.controls')
        .children('button.expand')
        .each(function () {
          let $button = $(this);
          let $icon = $button.children('i');
          let $expanders = $($button.data('target'));
          $icon.removeClass(expand_open_class).addClass(expand_closed_class);
          $expanders.slideUp(function () {
            $target.css('overflow', 'auto');
          });
        });
    });

    // Expand all button
    $(document).on('click', '.expand-all', function () {
      let $target = $($(this).data('target'));
      $target.css('overflow', 'hidden');
      $target
        .children('.content-block-form')
        .children('.pos-rel')
        .children('.controls')
        .children('button.expand')
        .each(function () {
          let $button = $(this);
          let $icon = $button.children('i');
          let $expanders = $($button.data('target'));
          $icon.removeClass(expand_closed_class).addClass(expand_open_class);
          $expanders.slideDown(function () {
            $target.css('overflow', 'auto');
          });
        });
    });

    // Remove saved class on change
    $(document).on('change', '.cb-form', function () {
      let $btn = $(this);
      setSaveState($($btn.data('btn')), false);
    });

    // Save & Continue button
    let saving_all = false;
    $(document).on('click', '#save_continue', function () {
      let $loader = $($(this).data('loader'));
      saveAll($loader);
    });

    // Save & Exit button
    $(document).on('click', '#save_exit', function () {
      let return_url = $(this).data('return_url');
      let $loader = $($(this).data('loader'));
      saveAll($loader, function () {
        exit(return_url);
      });
    });

    // Publish button
    $(document).on('submit', '#publish_form', function () {
      let $form = $(this);
      let $loader = $($(this).data('loader'));

      saveAll($loader, function () {
        showStatus('Publishing content blocks');
        $form.ajaxSubmit({
          success: function (data) {
            hideLoader($loader);
            showStatus('Content blocks published');
          },
        });
      });

      return false;
    });

    // Discard changes button
    $(document).on('submit', '#discard_form', function (e) {
      e.preventDefault();
      let $btn = $(this);
      showPopup($btn, {
        css_class: 'small',
        content: $('#reset_popup_content').html(),
        confirm_callback: function ($popup) {
          let $loader = $($btn.data('loader'));
          let $target = $('#content-blocks-root');

          showLoader($loader);
          showStatus('Resetting content blocks');
          $btn.ajaxSubmit({
            success: function (data) {
              $('.content-block-form').remove();
              renderAjaxResponse(data, $target, true);
              toggleImportForm();
              hideLoader($loader);
              showStatus('Content blocks reset');
            },
          });
        },
      });

      return false;
    });

    // Functions
    function renderAjaxResponse(data, $target, append = false, callback) {
      // Handle ajax which returns html
      if (data.error) {
        console.log(data.error);
        return;
      }

      if (data.html) {
        if (append) {
          $target.append(data.html);
        } else {
          $target.html(data.html);
        }
        refreshDragonDrop();
        toggleImportForm();
      }

      if (callback) {
        return callback();
      }
    }

    function saveContentBlock($btn, saved_callback) {
      // Save a content block given it's save button.  Optionally call a callback on successful save.
      let $form = $($btn.data('form'));
      let $target = $($form.data('target'));
      let $loader = $($btn.data('loader'));
      showLoader($loader);
      let title = $form.find('.title h2').html();
      showStatus('Saving ' + title);
      $form.ajaxSubmit({
        success: function (data) {
          setSaveState($btn, data.saved);
          renderAjaxResponse(data, $target);
          hideLoader($loader);

          if (data.saved) {
            showStatus(title + ' saved');
          } else {
            showStatus('Please correct the errors');
          }

          if (saved_callback && data.saved) {
            return saved_callback();
          }
        },
        uploadProgress: function (event, position, total, percentComplete) {
          $loader.find('.progress-bar').width(percentComplete + '%');
        },
      });
    }

    function updateButtonLabel($cb_type_select, $cb_create_button_label) {
      // Update the text in the create content block form submit button to match the selected content block type
      $cb_create_button_label.html(
        $cb_type_select.children('option:selected').text(),
      );
    }

    function saveAll($loader, callback) {
      // Save all unsaved content blocks sequentially.
      if (saving_all) {
        return;
      }

      saving_all = true;
      showLoader($loader);
      showStatus('Saving all content blocks');
      expandAll();
      let $buttons = $('button.save').not('.saved');
      return saveNext($buttons, callback, $loader);
    }

    function saveForPreview($btn, callback) {
      // Save unsaved content blocks and nested blocks for preview
      let $buttons = $btn
        .closest('.content-block-form')
        .find('button.save')
        .not('.saved');
      return saveNext($buttons, callback);
    }

    function saveNext($buttons, callback, $loader, buttons) {
      // Used by save all to save sequentially then call callback if all saved OK or scroll to errors.
      let scroll_offset = 30;

      if (!buttons) buttons = $buttons.toArray();

      if (!buttons.length) {
        // Finished saving everything
        saving_all = false;
        let $unsaved = $buttons.not('.saved');
        if ($unsaved.length) {
          $('html').animate(
            { scrollTop: $unsaved.first().offset().top - scroll_offset },
            220,
          );
          showStatus('Please correct the errors');
        } else {
          showStatus('All content blocks saved');
          if (callback) {
            return callback();
          }
        }
        if ($loader) hideLoader($loader);
        return;
      }

      let $btn = $(buttons.shift());

      let $inline_loader = undefined;
      if (!$loader) {
        $inline_loader = $($btn.data('loader'));
        showLoader($inline_loader);
      }

      let $form = $($btn.data('form'));
      let $target = $($form.data('target'));

      $form.ajaxSubmit({
        success: function (data) {
          setSaveState($btn, data.saved);
          renderAjaxResponse(data, $target, false, function () {
            if ($inline_loader) hideLoader($inline_loader);
            saveNext($buttons, callback, $loader, buttons);
          });
        },
        uploadProgress: function (event, position, total, percentComplete) {
          let $progress_bar;
          if ($inline_loader) {
            $progress_bar = $inline_loader.find('.progress-bar');
          } else {
            $progress_bar = $loader.find('.progress-bar');
          }
          $progress_bar.width(percentComplete + '%');
        },
      });
    }

    function exit(return_url) {
      // Redirect user to url.
      window.location.href = return_url;
    }

    function exitAjax(data, return_url) {
      // ajax calls which exit the editor come through here incase of errors.
      if (data.error) {
        console.log(data.error);
        return;
      }

      exit(return_url);
    }

    let loader_timers = {};
    function showLoader($loader) {
      // Show a loader.  The loader starts invisible and becomes visible to the user after a short time.
      $loader.show();
      loader_timers[$loader.attr('id')] = setTimeout(function () {
        showSpinner($loader);
      }, 750);
    }

    function hideLoader($loader) {
      // Hide a loader
      $loader.find('.progress-bar').width('100%');
      $loader.hide().children('.bg').hide();
      clearTimeout(loader_timers[$loader.attr('id')]);
    }

    function showSpinner($loader) {
      // Make the loader visible to the user
      $loader.find('.progress-bar').width('0%');
      $loader.children('.bg').show();
    }

    function enforceLimits($content_block_wrapper) {
      // Disable delete and add nested block buttons in the wrapper based on min_num and max_num
      let min_num = $content_block_wrapper.data('min_num');
      let max_num = $content_block_wrapper.data('max_num');

      let num_blocks = $content_block_wrapper.children(
        '.content-block-form',
      ).length;

      let delete_buttons = $content_block_wrapper
        .children('.content-block-form')
        .find('button.delete');
      if (num_blocks <= min_num) {
        // Min num reached so disabled delete button.
        delete_buttons
          .children('i')
          .removeClass(delete_active_class)
          .addClass(delete_disabled_class);
      } else {
        delete_buttons
          .children('i')
          .removeClass(delete_disabled_class)
          .addClass(delete_active_class);
      }

      let nested_form = $content_block_wrapper
        .siblings('.cb-nested-create-form')
        .children('.nested-create-form');
      if (num_blocks >= max_num) {
        // Max num reached so disable nested form.
        nested_form.addClass('disabled');
      } else {
        nested_form.removeClass('disabled');
      }
    }

    function dragonDrop($content_block) {
      // Make a group of content blocks dragon sortable with jquery ui sortable.
      $content_block.sortable({
        axis: 'y',
        handle: '.move',
        cancel: '',
        containment: $content_block,
        update: function (event, ui) {
          let positions = $(this).sortable('serialize');
          ajaxDragonDrop(positions);
        },
      });
    }

    function ajaxDragonDrop(positions) {
      // Post to updated positions in db.
      $.ajax({
        data: { positions: positions },
        type: 'POST',
        url: settings.update_position_url,
      });
    }

    function refreshDragonDrop() {
      // Refresh dragon drops and create new for new content blocks.
      let $content_blocks = $('.content-blocks');
      $content_blocks.not('.ui-sortable').each(function () {
        dragonDrop($(this));
      });
      $content_blocks.sortable('refresh');
    }

    function expandAll() {
      // Opens all expanders
      $('.expander').slideDown();
      $('.' + expand_closed_class)
        .removeClass(expand_closed_class)
        .addClass(expand_open_class);
    }

    const saved_class = 'fa-floppy-disk';
    const unsaved_class = 'fa-floppy-disk-circle-xmark';
    function setSaveState($btn, saved) {
      // Update the save state of the save button and change the icon.
      $btn.removeClass('saved');

      let $icon = $btn.children('i');
      $icon.removeClass(saved_class + ' ' + unsaved_class);
      if (saved) {
        $btn.addClass('saved');
        $icon.addClass(saved_class);
      } else {
        $icon.addClass(unsaved_class);
      }
    }

    function loadPreview($btn) {
      // Render a content block and get the html via ajax
      let $target = $($btn.data('target'));
      let $iframe = $target.children('iframe');

      $iframe
        .iFrameResize({
          checkOrigin: false,
        })
        .on('load', function () {
          $target.slideDown().addClass('open');
          $iframe.off('load');
        });

      $iframe.attr('src', $iframe.data('src'));
    }

    function toggleImportForm() {
      let $cb_import_form = $('.cb-import-form');
      if ($('.content-block-form').length) {
        $cb_import_form.hide();
      } else {
        $cb_import_form.show();
      }
    }

    let $status_bar = $('div.status');
    let status_off = $status_bar.html();
    let $status_timer;
    function renderStatus(status) {
      $status_bar.fadeOut(function () {
        $(this).html(status).fadeIn();
      });
    }

    function showStatus(status) {
      clearTimeout($status_timer);
      renderStatus(status);
      $status_timer = setTimeout(function () {
        renderStatus(status_off);
      }, 5500);
    }

    return this;
  };
})(jQuery);
