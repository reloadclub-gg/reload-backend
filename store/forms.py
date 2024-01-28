from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from . import models


class BoxForm(forms.ModelForm):
    class Meta:
        model = models.Box
        fields = '__all__'

    def _clean_featured(self, featured, featured_image):
        if featured and not featured_image:
            raise ValidationError(_('Featured must have a featured image.'))

    def clean(self):
        cleaned_data = super().clean()
        featured = cleaned_data.get('featured')
        featured_image = cleaned_data.get('featured_image')
        self._clean_featured(featured, featured_image)


class CollectionForm(forms.ModelForm):
    class Meta:
        model = models.Collection
        fields = '__all__'

    def _clean_featured(self, featured, featured_image):
        if featured and not featured_image:
            raise ValidationError(_('Featured must have a featured image.'))

    def clean(self):
        cleaned_data = super().clean()
        featured = cleaned_data.get('featured')
        featured_image = cleaned_data.get('featured_image')
        self._clean_featured(featured, featured_image)


class ItemForm(forms.ModelForm):
    class Meta:
        model = models.Item
        fields = '__all__'

    def _clean_weapon(self, item_type, subtype, weapon):
        if item_type == models.Item.ItemType.WEAPON:
            valid_weapons = models.Item.WEAPON_TYPES.get(subtype)
            if not valid_weapons:
                weapon_subtypes = [
                    models.Item.SubType.PISTOLS,
                    models.Item.SubType.SMGS,
                    models.Item.SubType.SHOTGUNS,
                    models.Item.SubType.MACHINEGUNS,
                    models.Item.SubType.RIFLES,
                ]
                raise ValidationError(
                    _('Weapon subtype must be one of the following: ')
                    + ', '.join(weapon_subtypes)
                )

            if weapon not in valid_weapons:
                raise ValidationError(
                    _('Weapon must be one of the following: ')
                    + ', '.join(valid_weapons)
                )

        if weapon and item_type != models.Item.ItemType.WEAPON:
            raise ValidationError(_('To select a weapon, item must be a weapon type.'))

    def _clean_decorative(self, item_type, subtype, decorative_image):
        if item_type == models.Item.ItemType.DECORATIVE:
            if not decorative_image:
                raise ValidationError(_('Decorative must have a decorative image.'))

            decorative_subtypes = [
                models.Item.SubType.CARD,
                models.Item.SubType.PROFILE,
            ]
            if not subtype or subtype not in decorative_subtypes:
                raise ValidationError(
                    _('Decorative subtype must be one of the following: ')
                    + ', '.join(decorative_subtypes)
                )

        if decorative_image and item_type != models.Item.ItemType.DECORATIVE:
            raise ValidationError(
                _('To upload a decorative image, item must be a decorative type.')
            )

    def _clean_wear(self, item_type, subtype):
        if item_type == models.Item.ItemType.WEAR:
            wear_subtypes = [models.Item.SubType.DEF, models.Item.SubType.ATA]
            if not subtype or subtype not in wear_subtypes:
                raise ValidationError(
                    _('Wear subtype must be one of the following: ')
                    + ', '.join(wear_subtypes)
                )

    def _clean_featured(self, featured, featured_image):
        if featured and not featured_image:
            raise ValidationError(_('Featured must have a featured image.'))

    def _clean_box_chance(self, box, box_draw_chance):
        if box:
            total_chance = (
                models.Item.objects.filter(box=box).aggregate(
                    models.Sum('box_draw_chance')
                )['box_draw_chance__sum']
                or 0
            )

            if total_chance + box_draw_chance > 100:
                raise ValidationError(
                    _('The total sum of items on this box cannot be greater then 100%.')
                )

    def clean(self):
        cleaned_data = super().clean()
        item_type = cleaned_data.get('item_type')
        subtype = cleaned_data.get('subtype')
        weapon = cleaned_data.get('weapon')
        decorative_image = cleaned_data.get('decorative_image')
        featured = cleaned_data.get('featured')
        featured_image = cleaned_data.get('featured_image')
        box = cleaned_data.get('box')
        box_draw_chance = cleaned_data.get('box_draw_chance')

        self._clean_weapon(item_type, subtype, weapon)
        self._clean_decorative(item_type, subtype, decorative_image)
        self._clean_wear(item_type, subtype)
        self._clean_featured(featured, featured_image)
        self._clean_box_chance(box, box_draw_chance)

        return cleaned_data
