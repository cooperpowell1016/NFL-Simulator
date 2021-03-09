from django import forms

class FootballTeamsForm(forms.Form):
    team_1 = forms.CharField(help_text="Enter Team 1 to simulate")
    year_1 = forms.IntegerField(help_text="Enter the year of Team 1")
    team_2 = forms.CharField(help_text="Enter Team 2 to simulate")
    year_2 = forms.IntegerField(help_text="Enter the year of Team 2")