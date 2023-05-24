import requests
import settings
from tqdm import tqdm
import json


class VK:

    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version,
        }
        self.images = []

    def get_photos(self, user_id=None):
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': 1,
        }
        response = requests.get(get_photos_url, params={**self.params, **get_photos_params}, ).json()

        for element in response['response']['items']:
            url = element['sizes'][-1]['url']
            size = element['sizes'][-1]['height'] * element['sizes'][-1]['width']
            likes_count = element['likes']['count']
            date = element['date']
            self.images.append({
                'file_name': f"{likes_count}" if not self.does_imagelist_contain_filename(likes_count) else
                f"{likes_count}_{date}",
                'size': size,
                'url': url,
            })
        self.images = sorted(self.images, key=lambda x: x['size'], reverse=True)[:settings.yd_photo_count]

    def does_imagelist_contain_filename(self, filename):
        for element in self.images:
            if element['file_name'] == str(filename):
                return True
        return False

    def save_photo_info_to_a_file(self, filename='log.json'):
        json_file = json.dumps(self.images, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_file)


class YaUploader:

    host = 'https://cloud-api.yandex.net/'

    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Content_Type': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def new_folder_create(self, folder_name):
        uri = 'v1/disk/resources/'
        url = self.host + uri
        params = {
            'path': f'/{folder_name}',
            'overwrite': 'true'
        }
        requests.put(url, headers=self.get_headers(), params=params)

    def upload_file_from_vk(self, file_url, file_name, folder_name):
        uri = 'v1/disk/resources/upload'
        url = self.host + uri
        params = {
            'path': f'/{folder_name}/{file_name}',
            'url': file_url, 'overwrite': 'true'
        }
        resp = requests.post(url=url, headers=self.get_headers(), params=params)
        if resp.status_code == 202:
            print(f'Файл {file_name} успешно загружен!')


if __name__ == '__main__':
    vk_user = VK(settings.vk_token, version='5.131')
    vk_user.get_photos(settings.owner_id)
    vk_user.save_photo_info_to_a_file()

    uploader = YaUploader(settings.yd_token)
    uploader.get_headers()

    folder_name = '20230524'
    uploader.new_folder_create(folder_name)

    for i in tqdm(range(len(vk_user.images))):
        file = vk_user.images[i]
        uploader.upload_file_from_vk(file['url'], file['file_name'], folder_name)
