window.addEventListener('load', function () {
  let $ = django.jQuery;
  // CHOICES WIDGET //
  let $row = $('.input-row').first();

  $('.choices-widget').each(function () {
    loadChoices($(this));
  });

  $(document).on('click', '.delete-choice-row', function (e) {
    e.preventDefault();
    let $choices_widget = $(this).closest('.choices-widget');
    $(this).parent().remove();
    saveChoices($choices_widget);
  });

  $(document).on('click', '.add-choice-row', function (e) {
    e.preventDefault();
    let $choices_widget = $(this).closest('.choices-widget');
    addRow($choices_widget);
  });

  $(document).on('change', '.choices-widget .input-row input', function () {
    let $choices_widget = $(this).closest('.choices-widget');
    saveChoices($choices_widget);
  });

  function loadChoices($choices_widget) {
    let $input = $choices_widget.find('input[type=hidden]');
    let choices = $input.val();

    if (!choices || choices === '[]') return;

    $choices_widget.find('.input-row').remove();

    choices = JSON.parse(choices);

    $.each(choices, function () {
      addRow($choices_widget, this);
    });
  }

  function saveChoices($choices_widget) {
    let $rows = $choices_widget.find('.input-row');
    let choices = [];

    $rows.each(function () {
      let $inputs = $(this).find('input');

      let val_1 = $inputs.first().val();
      let val_2 = $inputs.last().val();

      if (!val_1 || !val_2) return;

      choices.push([val_1, val_2]);
    });

    choices = JSON.stringify(choices);

    $choices_widget.find('input[type=hidden]').val(choices);
  }

  function addRow($choices_widget, values) {
    if (values === undefined) {
      values = ['', ''];
    }

    let $new_row = $row.clone();
    $new_row.find('input').each(function (i) {
      $(this).val(values[i]);
    });

    $choices_widget.find('.inputs').append($new_row);
  }
});
