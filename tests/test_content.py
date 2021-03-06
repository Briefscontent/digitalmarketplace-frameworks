import glob

import mock
import pytest

from dmcontent import ContentLoader
from dmcontent.utils import TemplateField

content = ContentLoader('./')

MANIFEST_QUESTION_SET = {
    "display_brief": "briefs",
    "edit_brief": "briefs",

    "display_brief_response": "brief-responses",
    "edit_brief_response": "brief-responses",
    "output_brief_response": "brief-responses",

    "clarification_question": "clarification_question",

    "declaration": "declaration",

    "display_service": "services",
    "edit_service": "services",
    "edit_service_as_admin": "services",
    "edit_submission": "services",
    "search_filters": "services",
}

QUESTION_SET_CONTEXT = {
    'briefs': {'lot': 'context-lot'},
    'brief-responses': {'lot': 'context-lot', 'brief': mock.Mock()},
    'services': {'lot': 'context-lot'},
}


def get_manifests():
    paths = glob.glob('frameworks/*/manifests/*.yml')
    for path in paths:
        _, framework, _, manifest = path.split('/')
        manifest = manifest.replace('.yml', '')

        yield (framework, MANIFEST_QUESTION_SET[manifest], manifest)


def content_questions():
    for manifest in get_manifests():
        content.load_manifest(*manifest)

    for framework, framework_questions in content._questions.items():
        for question_set, questions in framework_questions.items():
            for question in questions.values():
                yield framework, question_set, question['id'], question


def content_sections():
    for manifest in get_manifests():
        content.load_manifest(*manifest)

    for framework, framework_manifests in content._content.items():
        for manifest, sections in framework_manifests.items():
            for section in sections:
                yield framework, manifest, section['slug'], section


@pytest.mark.parametrize("framework, manifest, section_slug, section", content_sections())
def test_render_section(framework, manifest, section_slug, section):
    for field in section.values():
        if isinstance(field, TemplateField):
            assert field.render(QUESTION_SET_CONTEXT.get(MANIFEST_QUESTION_SET[manifest])) is not None


@pytest.mark.parametrize("framework, question_set, question_id, question", content_questions())
def test_render_question(framework, question_id, question_set, question):
    question_set_context = {
        'briefs': {'lot': 'context-lot'},
        'brief-responses': {'lot': 'context-lot', 'brief': mock.Mock()},
        'services': {'lot': 'context-lot'},
    }

    brief_msg = "Brief questions must be single-line since they're used as <title>s: frameworks/{}/questions/{}/{}.yml"

    for field_name, field in question.items():
        if isinstance(field, TemplateField):
            rendered_field = field.render(question_set_context.get(question_set))
            rendered_md = TemplateField(field.source, markdown=True).render(question_set_context.get(question_set))
            rendered_text = TemplateField(field.source, markdown=False).render(question_set_context.get(question_set))
            assert rendered_field is not None

            assert (
                strip_paragraph_wrapper(rendered_md) == strip_paragraph_wrapper(rendered_field)
            ), "Single-line field probably contains markdown: frameworks/{}/questions/{}/{}.yml".format(
                framework, question_set, question_id
            )

            if field.markdown and question_set in ['briefs', 'brief-responses'] and field_name == 'question':
                assert strip_paragraph_wrapper(rendered_field) != rendered_text, brief_msg.format(
                    framework, question_set, question_id
                )


def strip_paragraph_wrapper(value):
    if value.startswith('<p>'):
        value = value[3:-4]

    return value
