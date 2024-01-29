from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.translation import gettext as _

from . import models


class BoxForm(forms.ModelForm):
    class Meta:
        model = models.Box
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        featured = cleaned_data.get('featured')
        featured_image = cleaned_data.get('featured_image')

        if featured and not featured_image:
            raise ValidationError(_('Featured must have a featured image.'))

        return cleaned_data


class CollectionForm(forms.ModelForm):
    class Meta:
        model = models.Collection
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        featured = cleaned_data.get('featured')
        featured_image = cleaned_data.get('featured_image')

        if featured and not featured_image:
            raise ValidationError(_('Featured must have a featured image.'))

        return cleaned_data


class ItemForm(forms.ModelForm):
    class Meta:
        model = models.Item
        fields = '__all__'

    def clean_decorative_image(self):
        item_type = self.cleaned_data.get('item_type')
        decorative_image = self.cleaned_data.get('decorative_image')

        if item_type == models.Item.ItemType.DECORATIVE and not decorative_image:
            raise ValidationError(_('Decorative must have a decorative image.'))

        return decorative_image

    def clean_preview_image(self):
        item_type = self.cleaned_data.get('item_type')
        preview_image = self.cleaned_data.get('preview_image')

        if item_type == models.Item.ItemType.DECORATIVE and not preview_image:
            raise ValidationError(_('Decorative must have a preview image.'))

        return preview_image

    def clean_subtype(self):
        item_type = self.cleaned_data.get('item_type')
        subtype = self.cleaned_data.get('subtype')

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
        elif item_type == models.Item.ItemType.WEAR:
            wear_subtypes = [models.Item.SubType.DEF, models.Item.SubType.ATA]
            if not subtype or subtype not in wear_subtypes:
                raise ValidationError(
                    _('Wear subtype must be one of the following: ')
                    + ', '.join(wear_subtypes)
                )

        return subtype

    def clean_weapon(self):
        item_type = self.cleaned_data.get('item_type')
        subtype = self.cleaned_data.get('subtype')
        weapon = self.cleaned_data.get('weapon')

        valid_weapons = models.Item.WEAPON_TYPES.get(subtype)

        if valid_weapons and item_type == models.Item.ItemType.WEAPON:
            if weapon not in valid_weapons:
                raise ValidationError(
                    _('Weapon must be one of the following: ')
                    + ', '.join(valid_weapons)
                )

        if weapon and item_type != models.Item.ItemType.WEAPON:
            raise ValidationError(_('To select a weapon, item must be a weapon type.'))

        return weapon

    def clean_box_draw_chance(self):
        box = self.cleaned_data.get('box')
        box_draw_chance = self.cleaned_data.get('box_draw_chance')

        if box_draw_chance and not box:
            raise ValidationError(_('Items with draw chance must have a Box.'))

        if box_draw_chance:
            total_chance = (
                models.Item.objects.filter(box=box)
                .exclude(id=self.instance.pk)
                .aggregate(Sum('box_draw_chance'))['box_draw_chance__sum']
                or 0
            )

            if total_chance + box_draw_chance > 100:
                raise ValidationError(
                    _(
                        f'The total sum of items on this box cannot be greater then 100% ({total_chance + box_draw_chance}).'
                    )
                )

        return box_draw_chance

    def clean(self):
        cleaned_data = super().clean()
        featured = cleaned_data.get('featured')
        featured_image = cleaned_data.get('featured_image')

        if featured and not featured_image:
            raise ValidationError(_('Featured must have a featured image.'))

        return cleaned_data
