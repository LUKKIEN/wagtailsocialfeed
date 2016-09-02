import json

import dateutil.parser
from django.db import models


class ModeratedItemManager(models.Manager):
    def get_or_create_for(self, original_post):
        """
        Get an existing `ModeratedItem` based on the original_post
        or create a new one if it cannot be found.

        :param original_post:
            The original post as a JSON string or encoded JSON object
        """
        original_obj = json.loads(original_post)

        posted = dateutil.parser.parse(original_obj['posted'])
        external_id = original_obj['id']
        return self.get_or_create(
            external_id=external_id,
            defaults=dict(
                posted=posted,
                external_id=external_id,
                content=original_post))
