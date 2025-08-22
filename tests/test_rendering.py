from cms.api import create_page
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.utils import get_object_edit_url, get_object_structure_url


class StructureBoardRenderingTestCase(CMSTestCase):
    def test_static_alias_in_structure_board(self):
        page = create_page("Test Page", template="static_alias.html", language="en", created_by=self.get_superuser())
        page_content = page.get_admin_content("en")
        preview = get_object_edit_url(page_content)
        structure = get_object_structure_url(page_content)

        with self.login_user_context(self.get_superuser()):
            self.client.get(
                preview
            )  # First get preview to create static alias declared in the template and all palceholders

            # Check if the static alias is rendered in the structure board
            response = self.client.get(structure)

            # Regular placeholder of page content object
            self.assertContains(response, '<div class="cms-dragbar-title" title="Content">')
            # Static alias placeholder
            self.assertContains(response, '<div class="cms-dragbar-title" title="Template_Example_Global_Alias_Code">')
            self.assertContains(response, "cms-dragarea-static-icon")
