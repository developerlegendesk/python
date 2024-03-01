from time import time

def ttl(days):
  return int(days) * 24 * 60 * 60 + int(time())



def render_event_row(template, data, fields):
  for field in fields:
    template = template.replace(f'__{field}__', str(data[field]))

  return template
