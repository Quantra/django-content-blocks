// Wait for Django jQuery to load, so we can use it.
window.addEventListener('load', function () {
  let $ = django.jQuery;

  const FIELD_TYPES = {
    NESTED_FIELD: 'NestedField',
    CHECKBOX_FIELD: 'CheckboxField',
    CHOICE_FIELD: 'ChoiceField',
    MODEL_CHOICE_FIELD: 'ModelChoiceField',
    CONTENT_FIELD: 'ContentField',
  };

  const FIELDS = {
    MODEL_CHOICE_CONTENT_TYPE: '.field-model_choice_content_type',
    NESTED_TEMPLATE: '.field-nested_templates',
    CHOICES: '.field-choices',
    REQUIRED: '.field-required',
    HELP_TEXT: '.field-help_text',
    CSS_CLASS: '.field-css_class',
    MIN_NUM: '.field-min_num',
    MAX_NUM: '.field-max_num',
  };

  const ALWAYS_HIDE = [
    FIELDS.MODEL_CHOICE_CONTENT_TYPE,
    FIELDS.NESTED_TEMPLATE,
    FIELDS.CHOICES,
    FIELDS.MIN_NUM,
    FIELDS.MAX_NUM,
  ];
  const ALWAYS_SHOW = [FIELDS.REQUIRED, FIELDS.HELP_TEXT, FIELDS.CSS_CLASS];

  let options = {};
  options[FIELD_TYPES.NESTED_FIELD] = {
    show: [FIELDS.NESTED_TEMPLATE, FIELDS.MIN_NUM, FIELDS.MAX_NUM],
    hide: [FIELDS.REQUIRED],
  };
  options[FIELD_TYPES.CHECKBOX_FIELD] = { hide: [FIELDS.REQUIRED] };
  options[FIELD_TYPES.CHOICE_FIELD] = { show: [FIELDS.CHOICES] };
  options[FIELD_TYPES.MODEL_CHOICE_FIELD] = {
    show: [FIELDS.MODEL_CHOICE_CONTENT_TYPE],
  };

  function showFields($field_type) {
    let $parent = $field_type.parents('.field-field_type');
    $parent.siblings(ALWAYS_HIDE.toString()).hide();
    $parent.siblings(ALWAYS_SHOW.toString()).show();

    let field_type = $field_type.val();

    let option = options[field_type];

    if (!option) {
      return;
    }

    let show = option.show;
    let hide = option.hide;

    if (show) {
      $parent.siblings(show.toString()).show();
    }

    if (hide) {
      $parent.siblings(hide.toString()).hide();
    }
  }

  $('.field-field_type select').each(function () {
    showFields($(this));
  });

  $(document).on('change', '.field-field_type select', function () {
    showFields($(this));
  });
});
