import csv
import os

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.utils.translation import get_language, ugettext_lazy, ugettext as _

from student.models import CourseEnrollment
from student.models import get_user_by_username_or_email

import logging
log = logging.getLogger(__name__)

def validate_file_extension(file):
    ext = os.path.splitext(file.name)[1]
    valid_extensions = ['.csv']
    if not ext in valid_extensions:
        raise ValidationError(_('Unsupported file extension.'))

def get_default_delimiter():
    """Get the default csv delimiter according to the user's language."""
    return ','

class UploadGradesFileForm(forms.Form):
    grades_file = forms.FileField(label=ugettext_lazy("Grades file"), validators=[validate_file_extension])
    csv_delimiter = ','

    def __init__(self, *args, **kwargs):
        self.sga_block = kwargs.pop('sga_block', None)
        super(UploadGradesFileForm, self).__init__(*args, **kwargs)

    def clean_grades_file(self):
        grades_file = csv.DictReader(self.cleaned_data['grades_file'],
                                         ['username', 'fullname', 'filename', 'timestamp', 'fresh', 'finalized', 'date_fin', 'score', 'max_score', 'comment'],
                                         delimiter=',')
        for line, row in enumerate(grades_file):
            if self.is_user(line, row['username']) and line:    #pass first line
                self.check_user_enrollment(line, row['username'])
            if row['score'] and line:                           #pass first line
                self.check_score(line, row['score'])
            if row['finalized'] and line:                       #pass first line
                self.check_flag(line, row['finalized'])
            elif line:
                self.add_form_error(line, _(u"Student needs a score to be graded."))

    def is_user(self, line, username):
        if line:                                                #pass first line
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                self.add_form_error(line, _(u"User %s does not exist.") % username)
            else:
                return True

    def check_user_enrollment(self, line, username):
        user = get_user_by_username_or_email(username)
        if not CourseEnrollment.is_enrolled(user,
                                            self.sga_block.course_id):
            self.add_form_error(line, _(u"User %s is not enrolled to this course.") % username)

    def check_score(self, line, score):
        try:
            score = int(score)
        except ValueError:
            self.add_form_error(line, _(u"Score %s is not an integer.") % score)
        else:
            if not 0 <= score <= self.sga_block.max_score():
                self.add_form_error(line, _(u"Score %s is outside score limits.") % score)

    def check_flag(self, line, flag):
        try:
            flag = bool(flag)
        except ValueError:
            self.add_form_error(line, _(u"Finalized flag %s is not an boolean.") % flag)

    def add_form_error(self, line, error_description):
        if not self._errors.get('grades_file'):
            self._errors['grades_file'] = ErrorList()
        error_msg = _(u"Line %(line)s: %(error_description)s") % {'line' : line, 'error_description' : error_description}
        self._errors['grades_file'].append(error_msg)

