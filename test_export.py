import unittest
from export_images import select_secondary


class SelectionTests(unittest.TestCase):
    def test_excludes_main_and_its_query_variant(self):
        main = {'id': 1, 'position': 1, 'src': 'https://cdn.example/main.png?v=1'}
        duplicate = {'id': 2, 'position': 2, 'src': 'https://cdn.example/main.png?v=2'}
        secondary = {'id': 3, 'position': 3, 'src': 'https://cdn.example/detail.png'}
        selected, primary = select_secondary({'images': [secondary, duplicate, main]})
        self.assertEqual(primary, main)
        self.assertEqual(selected, [secondary])

    def test_single_and_empty(self):
        self.assertEqual(select_secondary({'images': []}), ([], None))
        self.assertEqual(select_secondary({'images': [{'id': 1, 'src': 'https://cdn.example/a.png'}]})[0], [])

    def test_explicit_main_is_also_excluded(self):
        images = [{'id': n, 'position': n, 'src': f'https://cdn.example/{n}.png'} for n in range(1, 4)]
        self.assertEqual(select_secondary({'images': images, 'image': images[1]})[0], [images[2]])


if __name__ == '__main__':
    unittest.main()
