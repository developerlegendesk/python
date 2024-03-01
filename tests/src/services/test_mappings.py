import unittest
from src.services import mappings


class TestMappings(unittest.TestCase):
  def test_get_field_name_main(self):
    data = [
      'field_64|email_address',
      'field_63|name',
      'field_114|ORGNAME',
      'field_179|country',
      'field_185|CITY',
      'field_184|state', # '_STATE',
      'field_229|LINKEDIN',

      'field_121|status',
      'field_167|last_changed',
      'field_283|newsletters',
      'field_294|promotions',

      # Radiology Business
      'field_289|newsletters',
      'field_295|promotions',

      # Cardiovascular Business
      'field_290|newsletters',
      'field_293|promotions',

      # Health Exec
      'field_267|newsletters',
      'field_292|promotions',

      # AI Healthcare
      'field_262|newsletters',
      'field_291|promotions'
    ]
    for item in data:
      with self.subTest(value = item):
        results = mappings.get_field_name(item.split('|')[0])
        self.assertEqual(results, item.split('|')[1])

  def test_get_field_name_from_list(self):
    data = [
      # 'name|Health Imaging',
      'status|field_247',
      'update|field_299',
      'active|field_252',
      'cleaned|field_260',
      'unsub|field_256',
      
      # 'name|Radiology Business',
      'status|field_249',
      'update|field_300',
      'active|field_253',
      'cleaned|field_261',
      'unsub|field_257',

      # 'name|Cardiovascular Business',
      'status|field_246',
      'update|field_298',
      'active|field_250',
      'cleaned|field_259',
      'unsub|field_255',

      # 'name|Health Exec',
      'status|field_248',
      'update|field_297',
      'active|field_251',
      'cleaned|field_258',
      'unsub|field_254',

      # 'name|AI Healthcare',
      'status|field_242',
      'update|field_296',
      'active|field_243',
      'cleaned|field_245',
      'unsub|field_244',
    ]
    for item in data:
      with self.subTest(value = item):
        results = mappings.get_field_name(item.split('|')[1])
        self.assertEqual(results, item.split('|')[0])
