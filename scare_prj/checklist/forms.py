from django import forms
from .models import Todo, Day

class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ('title', 'due_date', 'due_time', 'repeat_on')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '제목을 입력하세요.'}),
            'repeat_on': forms.CheckboxSelectMultiple,
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'due_time': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {
            'title' : '',
            'due_date': '날짜',
            'due_time' : '시간',
            'repeat_on' : '반복'
        }
