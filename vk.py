import requests
from settings import token, version
import vk_api

vk = vk_api.VkApi(token=token)
user_api = vk.get_api()


def search_partners(age_from, age_to, sex, city, offset):
    result = vk.method('users.search', {
        'offset': offset,
        'age_from': age_from,
        'age_to': age_to,
        'sex': sex,
        'city': city,
        'status': 6,
        'has_photo': 1
    })
    for items in result['items']:
        is_closed = items['is_closed']
        if is_closed:
            offset += 1
        else:
            return items


def photo_request(user_id):
    result = requests.get(
        'https://api.vk.com/method/photos.get',
        {
            'owner_id': user_id,
            'album_id': 'profile',
            'access_token': token,
            'v': version,
            'extended': 1,
            'photos_sizes': 1
        })
    all_photos = []
    sorted_res = sorted(result.json()['response']['items'], key=lambda x: x['likes']['count'], reverse=True)
    for id_photo in sorted_res:
        all_photos.append(f"photo{user_id}_{id_photo['id']}")
    photos = ','.join(all_photos[:3])
    return photos
