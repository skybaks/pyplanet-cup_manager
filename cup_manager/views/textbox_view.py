

from pyplanet.views.template import TemplateView


class TextboxView(TemplateView):

	template_name = 'cup_manager/textbox.xml'


	def __init__(self, app):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.id = 'cup_manager__textbox_textboxview'


