import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image, AsyncImage
from kivy.core.window import Window
from kivy.graphics import Color, Rotate, PushMatrix, PopMatrix
import pickle
from kivy.uix.filechooser import FileChooserIconView
from android.permissions import request_permissions, Permission
import platform
from kivy.uix.popup import Popup
from kivy.clock import Clock
import os
import shutil
from PIL import Image


class ChooseImagePopup(Popup):
	def __init__(self, **kwargs):
		super(ChooseImagePopup, self).__init__(**kwargs)
		self.ids.id_FileChooser.path = '/storage/emulated/0/DCIM'  # Set the default path to DCIM folder
		
	def select_image(self, selection):
		if selection:
			app = App.get_running_app()
			selected_image_path = selection[0]
			destination_dir = "ProjectImages/" + app.currentProjectName + "/"
			os.makedirs(destination_dir, exist_ok=True)
			image_name = os.path.basename(selected_image_path)
			destination_path = os.path.join(destination_dir, image_name)
			destination_path = self.get_unique_filename(destination_path)
			shutil.copy(selected_image_path, destination_path)
			self.downscale_image(destination_path, 256, 256)
			if app.current_row:
				previous_image_path = app.current_row.ids.id_imageRowItem.source
				if previous_image_path and os.path.exists(previous_image_path):
					os.remove(previous_image_path)
				app.current_row.ids.id_imageRowItem.source = destination_path
				app.current_row = None
			self.dismiss()
		
	def downscale_image(self, image_path, width, height):
		with Image.open(image_path) as img:
			img = img.resize((width, height), Image.LANCZOS)
			img.save(image_path)
			
	def get_unique_filename(self, filepath):
		directory, filename = os.path.split(filepath)
		name, ext = os.path.splitext(filename)
		counter = 1
		while os.path.exists(filepath):
			if name[-1].isdigit():
				base_name = name.rstrip('0123456789')
				number = int(name[len(base_name):]) + 1
				name = f"{base_name}{number}"
			else:
				name = f"{name}1"
			filepath = os.path.join(directory, f"{name}{ext}")
		return filepath
			
			
class ProjectSavesRow(BoxLayout):
	def delete_save(self):
		self.parent.remove_widget(self)
		app = App.get_running_app()
		app.save_saves()
		self.delete_file()
		
	def delete_file(self):
		_saveFileToDelete = os.path.join('ProjectSaves', self.ids.id_buttonProjectSave.text + '.pickle')
		if os.path.isfile(_saveFileToDelete):
			os.remove(_saveFileToDelete)
			
	def load_project(self):
		app = App.get_running_app()
		app.currentProjectName = self.ids.id_buttonProjectSave.text
		self.parent.parent.parent.parent.ids.id_labelProjectTitle.text = app.currentProjectName
		app.root.load_project()
		
	def save_project(self):
		app = App.get_running_app()
		app.currentProjectName = self.ids.id_buttonProjectSave.text
		self.parent.parent.parent.parent.ids.id_labelProjectTitle.text = app.currentProjectName
		app.root.save_project()
		
	def shift_row_up(self):
		parent = self.parent
		index = parent.children.index(self)
		if index < len(parent.children) - 1:
			parent.remove_widget(self)
			parent.add_widget(self, index + 1)
		
	def shift_row_down(self):
		parent = self.parent
		index = parent.children.index(self)
		if index > 1:
			parent.remove_widget(self)
			parent.add_widget(self, index - 1)
	
	pass


class ProjectSavesGroup(BoxLayout):
	def saveAs_project(self):
		app = App.get_running_app()
		_saveName = self.ids.id_inputProjectSaveName.text
		_projectSavesRow = ProjectSavesRow()
		existing_names = {save.ids.id_buttonProjectSave.text for save in self.ids.id_containerSaves.children if 'id_buttonProjectSave' in save.ids}
		_base = _saveName.rstrip('0123456789')
		counter = 1
		if _saveName in existing_names:
			while _saveName in existing_names:
				_saveName = f"{_base}{counter}"
				counter += 1
				app.currentProjectName = _saveName
				self.ids.id_buttonSaveProject.text = app.currentProjectName
			_projectSavesRow.ids.id_buttonProjectSave.text = app.currentProjectName
			self.ids.id_inputProjectSaveName.text = ''
			self.ids.id_containerSaves.add_widget(_projectSavesRow)
			app.root.save_project()
			_savesFilename = 'project_saves.pickle'
			_savesList = []
			for save in reversed(self.ids.id_containerSaves.children):
				if 'id_buttonProjectSave' in save.ids:
					_saveData = {
						'ProjectSave': save.ids.id_buttonProjectSave.text
					}
					_savesList.append(_saveData)
			with open(_savesFilename, 'wb') as file:
				pickle.dump(_savesList, file)
			return _saveName
		else:
			app.currentProjectName = _saveName
			_projectSavesRow = ProjectSavesRow()
			_projectSavesRow.ids.id_buttonProjectSave.text = app.currentProjectName
			self.ids.id_inputProjectSaveName.text = ''
			self.ids.id_containerSaves.add_widget(_projectSavesRow)
			app.root.save_project()
			_savesFilename = 'project_saves.pickle'
			_savesList = []
			for save in reversed(self.ids.id_containerSaves.children):
				if 'id_buttonProjectSave' in save.ids:
					_saveData = {
						'ProjectSave': save.ids.id_buttonProjectSave.text
					}
					_savesList.append(_saveData)
			with open(_savesFilename, 'wb') as file:
				pickle.dump(_savesList, file)
			return _saveName
			
	def load_projectSaves(self):
		if not os.path.exists('project_saves.pickle'):
			with open('project_saves.pickle', 'wb') as file:
				pickle.dump([], file)
			return
		with open('project_saves.pickle', 'rb') as file:
			_projectSaves = pickle.load(file)
			for _projectSave in _projectSaves:
				_projectSavesRow = ProjectSavesRow()
				_projectSavesRow.ids.id_buttonProjectSave.text = _projectSave['ProjectSave']
				self.ids.id_containerSaves.add_widget(_projectSavesRow)
				
	def save_saves(self):
		_savesFilename = 'project_saves.pickle'
		_savesList = []
		for save in reversed(self.ids.id_containerSaves.children):
			if 'id_buttonProjectSave' in save.ids:
				_saveData = {
					'ProjectSave': save.ids.id_buttonProjectSave.text
				}
				_savesList.append(_saveData)
		with open(_savesFilename, 'wb') as file:
			pickle.dump(_savesList, file)
				
	pass
	
	
class Row(BoxLayout):
	toggleRowLock = BooleanProperty(False)
	toggleRowPurchased = BooleanProperty(False)
	
	def toggle_rowLock(self):
		self.toggleRowLock = not self.toggleRowLock
		
	def toggle_rowPurchased(self):
		self.toggleRowPurchased = not self.toggleRowPurchased
		if self.toggleRowPurchased == True:
			self.ids.id_buttonPurchased.text = '1'
		else:
			self.ids.id_buttonPurchased.text = '0'
		app = App.get_running_app()
		app.calculate_cost()
		
	def delete_row(self):
		self.parent.remove_widget(self)
		app = App.get_running_app()
		app.refresh_project()
		
	def shift_row_up(self):
		parent = self.parent
		index = parent.children.index(self)
		if index < len(parent.children) - 1:
			parent.remove_widget(self)
			parent.add_widget(self, index + 1)
		
	def shift_row_down(self):
		parent = self.parent
		index = parent.children.index(self)
		if index > 1:
			parent.remove_widget(self)
			parent.add_widget(self, index - 1)
			
	def handling_emptyInput(self):
		_inputPrice = self.ids.id_inputRowPrice
		_inputQuantity = self.ids.id_inputRowQuantity
		if _inputQuantity.focused:
			if _inputQuantity.text.isdigit() and float(_inputQuantity.text) == 0:
				_inputQuantity.text = _inputQuantity.text.replace("0","")
		else:
			if _inputQuantity.text == "":
				_inputQuantity.text = "0"
		if _inputPrice.focused:
			_inputPrice.text = _inputPrice.text.replace("$","")
			if _inputPrice.text in [".", "-","-."]:
				_inputPrice.text = "0.00"
			elif "-" in _inputPrice.text:
				if float(_inputPrice.text.replace("-","0")) == 0:
					_inputPrice =""
				else:
					_inputPrice.text = _inputPrice.text.split(".")[0] + "." + _inputPrice.text.split(".")[1]
			elif float(_inputPrice.text.replace("","0")) == 0:
				_inputPrice.text = ""
			else:
				_inputPrice.text = _inputPrice.text.split(".")[0] + "." + _inputPrice.text.split(".")[1]
		else:
			if _inputPrice.text in [".", "-","-."]:
				_inputPrice.text = "$0.00"
			elif _inputPrice.text == "":
				_inputPrice.text = "$0.00"
			else:
				_inputPrice.text = f'${float(_inputPrice.text.replace("$","")):.2f}'
		_labelTotalPrice = self.ids.id_labelRowTotalPrice
		if _inputPrice.text == "" or _inputQuantity.text == "":
			_labelTotalPrice.text = "$0.00"
		else:
			_labelTotalPrice.text = f'${(float(_inputPrice.text.replace("$",""))) * (float(_inputQuantity.text)):.2f}'
		app = App.get_running_app()
		self.ids.id_buttonPurchased.trigger_action()
		self.ids.id_buttonPurchased.trigger_action()
		
	def open_file_chooser(self):
		app = App.get_running_app()
		app.current_row = self
		app.open_image_popup()
		
	pass


class Group(BoxLayout):
	toggleGroup = BooleanProperty(True)
	
	def toggle_Group(self):
		self.toggleGroup = not self.toggleGroup
		
	def add_row(self, rowDescription=''):
		_newRow = Row()
		_newRow.ids.id_inputRowDescription.text = rowDescription
		self.ids.id_containerRows.add_widget(_newRow, index=1)
		
	def delete_group(self):
		self.parent.remove_widget(self)
		app = App.get_running_app()
		app.refresh_project()
		
	def shift_row_up(self):
		parent = self.parent
		index = parent.children.index(self)
		if index < len(parent.children) - 1:
			parent.remove_widget(self)
			parent.add_widget(self, index + 1)
		
	def shift_row_down(self):
		parent = self.parent
		index = parent.children.index(self)
		if index > 0:
			parent.remove_widget(self)
			parent.add_widget(self, index - 1)
		
	def calculate_priceGroup(self):
		_groupPrice = 0
		_groupPurchasedPrice = 0
		for row in reversed(self.ids.id_containerRows.children):
			if 'id_labelRowTotalPrice' in row.ids:
				try:
					_groupPurchasedPrice += float(row.ids.id_labelRowTotalPrice.text.replace('$','')) * float(row.ids.id_buttonPurchased.text)
					_groupPrice += float(row.ids.id_labelRowTotalPrice.text.replace('$',''))
				except ValueError:
					pass
		self.ids.id_labelGroupPrice.text = f'$ {_groupPrice:.2f}'
		self.ids.id_labelGroupPurchasedPrice.text = str(_groupPurchasedPrice)
		
	def save_project(self, filename='t.pickle'):
		rows_data = []
		for row in reversed(self.ids.id_containerRows.children):
			if 'id_inputRowDescription' in row.ids:
				row_data = {
					'rowDescription': row.ids.id_inputRowDescription.text
				
				}
				rows_data.append(row_data)
		with open(filename, 'wb') as file:
			pickle.dump(rows_data, file)
		
	def load_project(self, filename='t.pickle'):
		try:
			with open(filename, 'rb') as file:
				rows_data = pickle.load(file)
			for row_data in rows_data:
				self.add_row(row_data['rowDescription'])
		except FileNotFoundError:
			pass
		
	pass


class SetupPlanner(BoxLayout):
	def __init__(self, **kwargs):
		super(SetupPlanner, self).__init__(**kwargs)
		
	def new_project(self):
		self.ids.id_containerGroups.clear_widgets()
		
	def add_Group(self, groupTitle=''):
		_newGroup = Group()
		_newGroup.ids.id_labelGroupTitle.text = groupTitle
		self.ids.id_containerGroups.add_widget(_newGroup, index=0)
		
	def save_project(self, filename='t.pickle'):
		app = App.get_running_app()
		filename = 'ProjectSaves/' + app.currentProjectName + '.pickle'
		self.ids.id_labelProjectTitle.text = app.currentProjectName #filename[:-7]
		self.move_images()
		project_data = {
			'groups_data': [
				{
					'group_Title': group.ids.id_labelGroupTitle.text,
					'group_Title2': group.ids.id_labelGroupTitle2.text,
					'rows_data': [
						{
							'rowTitle': row.ids.id_inputRowItemTitle.text,
							'rowDescription': row.ids.id_inputRowDescription.text,
							'rowImage': row.ids.id_imageRowItem.source,
							'rowPrice': row.ids.id_inputRowPrice.text,
							'rowQuantity': row.ids.id_inputRowQuantity.text,
							'rowPurchased': row.toggleRowPurchased,
							'rowLocked': row.toggleRowLock
						} for row in reversed(group.ids.id_containerRows.children) if 'id_inputRowDescription' in row.ids
					]
				} for group in reversed(self.ids.id_containerGroups.children)
			]
		}
		with open(filename, 'wb') as file:
			pickle.dump(project_data, file)
		app.back_toProject()
			
	def load_project(self, filename='t.pickle'):
		app = App.get_running_app()
		filename = 'ProjectSaves/' + app.currentProjectName + '.pickle'
		try:
			with open(filename, 'rb') as file:
				project_data = pickle.load(file)
			self.ids.id_containerGroups.clear_widgets()
			for group_data in project_data['groups_data']:
				group = Group()
				if 'id_labelGroupTitle' in group.ids:
					group.ids.id_labelGroupTitle.text = group_data['group_Title']
					group.ids.id_labelGroupTitle2.text = group_data['group_Title2']
				for row_data in reversed(group_data['rows_data']):
					row = Row()
					if 'id_inputRowDescription' in row.ids:
						row.ids.id_inputRowItemTitle.text = row_data['rowTitle']
						row.ids.id_inputRowDescription.text = row_data['rowDescription']
						row.ids.id_imageRowItem.source = row_data['rowImage']
						row.ids.id_inputRowPrice.text = row_data['rowPrice']
						row.ids.id_inputRowQuantity.text = row_data['rowQuantity']
						row.toggleRowPurchased = row_data['rowPurchased']
						row.toggleRowLock = row_data['rowLocked']
					row.ids.id_buttonPurchased.trigger_action()
					row.ids.id_buttonPurchased.trigger_action()
					row.handling_emptyInput()
					group.ids.id_containerRows.add_widget(row, index=len(group.ids.id_containerRows.children))
				self.ids.id_containerGroups.add_widget(group)
		except FileNotFoundError:
			app.back_toProject()
			pass
		app.back_toProject()
		
	def move_images(self):
		app = App.get_running_app()
		for group in reversed(self.ids.id_containerGroups.children):
			for row in reversed(group.ids.id_containerRows.children):
				if 'id_imageRowItem' in row.ids:
					_imagePath = row.ids.id_imageRowItem.source
					if os.path.exists(_imagePath):
						_imagePathNew = os.path.join('ProjectImages/', app.currentProjectName, os.path.basename(_imagePath))
						if _imagePath != _imagePathNew:
							os.makedirs(os.path.dirname(_imagePathNew), exist_ok=True)
							shutil.copy(_imagePath, _imagePathNew)
							row.ids.id_imageRowItem.source = os.path.join('ProjectImages/', app.currentProjectName, os.path.basename(row.ids.id_imageRowItem.source))
					else:
						row.ids.id_imageRowItem.source = ''#os.path.join('ProjectImages/', app.currentProjectName, '')
						pass
						
	def delete_images(self):
		app = App.get_running_app()
		for group in reversed(self.ids.id_containerGroups.children):
			for row in reversed(group.ids.id_containerRows.children):
				pass
		
	def imgtest(self):
		app = App.get_running_app()
		for group in reversed(self.ids.id_containerGroups.children):
			for row in reversed(group.ids.id_containerRows.children):
				if 'id_imageRowItem' in row.ids:
					a = row.ids.id_imageRowItem.source
					row.ids.id_inputRowDescription.text = str(a)
				#	if row.ids.id_imageRowItem.source == 'a.png':
#						row.ids.id_imageRowItem.opacity = 0
#					else:
#						row.ids.id_imageRowItem.opacity = 1
			
	pass
	
	
class MyApp(App):
	def on_start(self):
		self.calculate_cost()
		self.root.ids.id_ProjectSavesGroup.load_projectSaves()
		
	def refresh_project(self):
#		for group in reversed(self.root.ids.id_containerGroups.children):
#			group.calculate_priceGroup()
		#Group().calculate_priceGroup()
		row = Row()
		row.ids.id_buttonPurchased.trigger_action()
	#	row.ids.id_buttonPurchased.trigger_action()
	
	def save_saves(self):
		self.root.ids.id_ProjectSavesGroup.save_saves()

	def calculate_cost(self):
		_totalCost = 0
		_totalCostPurchased = 0
		for group in reversed(self.root.ids.id_containerGroups.children):
			group.calculate_priceGroup()
			if 'id_labelGroupPrice' in group.ids:
				try:
					_totalCost += float(group.ids.id_labelGroupPrice.text.replace('$',''))
					_totalCostPurchased += float(group.ids.id_labelGroupPurchasedPrice.text.replace('$',''))
				except ValueError:
					pass
		self.root.ids.id_totalCost.text = f'$ {_totalCost:.2f}'
		self.root.ids.id_totalPurchased.text = f'$ {_totalCostPurchased:.2f}'
		self.root.ids.id_totalNotPurchased.text = f'$ {_totalCost - _totalCostPurchased:.2f}'

	windowSize = Window.size
	windowSizeX = float(windowSize[0])
	windowSizeY = float(windowSize[1])
	
#	windowSizeX = 1000
#	windowSizeY = 2000

	phi  =  ((1+(5**(1/2)))/2)
	Size1 = windowSizeX * (1/(phi**(1)))
	Size2 = windowSizeX * (1/(phi**(2)))
	Size3 = windowSizeX * (1/(phi**(3)))
	Size4 = windowSizeX * (1/(phi**(4)))
	Size5 = windowSizeX * (1/(phi**(5)))
	Size6 = windowSizeX * (1/(phi**(6)))
	Size7 = windowSizeX * (1/(phi**(7)))
	Size8 = windowSizeX * (1/(phi**(8)))
	Size9 = windowSizeX * (1/(phi**(9)))
	Size10 = windowSizeX * (1/(phi**(10)))
	Size11 = windowSizeX * (1/(phi**(11)))
	Size12 = windowSizeX * (1/(phi**(12)))
	Size13 = windowSizeX * (1/(phi**(13)))
	
	colorMain1 = tuple(Color(266/360,90/100,85/100, mode='hsv').rgba)
	colorMain2 = tuple(Color(256/360,30/100,95/100, mode='hsv').rgba)
	colorDeleteButton = tuple(Color(0/360,95/100,90/100, mode='hsv').rgba)
	
	colorA = tuple(Color(120/360,50/100,100/100, mode='hsv').rgba)
	
	colorBackground1 = tuple(Color(225/360,19/100,8/100, mode='hsv').rgba)
	colorBackground2 = tuple(Color(223/360,20/100,14/100, mode='hsv').rgba)
	colorBackground3 = tuple(Color(221/360,21/100,20/100, mode='hsv').rgba)
	
	colorText1 = tuple(Color(220/360,2/100,67/100, mode='hsv').rgba)
	colorText2 = tuple(Color(230/360,6/100,88/100, mode='hsv').rgba)
	colorText3 = tuple(Color(220/360,0/100,92/100, mode='hsv').rgba)
	
	colorTextInputRow = colorBackground2#tuple(Color(270/360,1/100,17/100, mode='hsv').rgba)
	
	
	fontName_Oxygen = "Fonts/Oxygen/Oxygen_Regular.ttf"
	
	fontSize_Titles1 = '50'
	
	toggleMenu = BooleanProperty(False)
	toggleMenuColor = BooleanProperty(False)
	toggleGroup = BooleanProperty(True)
	toggleGroupEdit = BooleanProperty(False)
	toggleRowDelete = BooleanProperty(False)
	toggleSaveDelete = BooleanProperty(False)
	toggleProjectSaveAs = BooleanProperty(False)
	toggleProjectLoad = BooleanProperty(False)
	toggleProjectSaves = BooleanProperty(False)
	current_row = None
	currentProjectName = ''
	
	def toggle_menu(self):
		self.toggleMenu = not self.toggleMenu
		
	def toggle_menuColor(self):
		self.toggleMenuColor = not self.toggleMenuColor
		
	def toggle_group(self):
		self.toggleGroup = not self.toggleGroup
		
	def toggle_groupEdit(self):
		self.toggleGroupEdit = not self.toggleGroupEdit
		
	def toggle_rowDelete(self):
		self.toggleRowDelete = not self.toggleRowDelete
		
	def toggle_saveDelete(self):
		self.toggleSaveDelete = not self.toggleSaveDelete
		
	def toggle_projectSaveAs(self):
		self.toggleProjectSaveAs = True #not self.toggleProjectSaveAs
		self.toggleProjectSaves = True #not self.toggleProjectSaves
		self.toggleProjectLoad = False
		self.toggleMenu = False
		
	def toggle_projectLoad(self):
		self.toggleProjectLoad = True #not self.toggleProjectLoad
		self.toggleProjectSaves = True
		self.toggleProjectSaveAs = False
		self.toggleMenu = False
		
	def back_toProject(self):
		self.toggleProjectLoad = False #not self.toggleProjectLoad
		self.toggleProjectSaves = False
		self.toggleProjectSaveAs = False
		self.toggleMenu = False

	def open_image_popup(self):
		popup = ChooseImagePopup()
		popup.open()

	
	def build(self):
		return SetupPlanner()
	
if __name__ == '__main__':
	MyApp().run()