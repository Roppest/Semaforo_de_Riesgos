import requests
import datetime
import time
import os
import subprocess
import sys

try :
	from bs4 import BeautifulSoup as soup
except ImportError:
	subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
	subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'lxml'])
finally:
	from bs4 import BeautifulSoup as soup
	import bs4
# TODO: May face concurrency issues if the files are accesed
# replace 10:29 with a variable or think of a better way to get the date
'''
Here is an example of the data this scraper is working with.
<?xml version="1.0"?>
<rss version="2.0" xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#">
<channel>
<title>Últimos sismos registrados por el SSN</title>
<link/>http://www.ssn.unam.mx
		<description>Reporte de los últimos sismos en México</description>

    <item>
        <title>4.1, 70 km al SUROESTE de TAPACHULA, CHIS </title>
        <description>
            <p>Fecha:2020-10-04 10:49:42 (Hora de M&eacute;xico)<br/>Lat/Lon:
            14.61/-92.84<br/>Profundidad: 68.0 km
            </p>
        </description>
        <link>
            http://www2.ssn.unam.mx:8080/jsp/localizacion-de-sismo.jsp?
            latitud=14.61&longitud=-92.84&prf=68.0 km&ma=4.1&fecha=2020-10-04&hora=10:49:42&loc=70
             km al SUROESTE de TAPACHULA, CHIS &evento=1
        </link>
        <geo:lat>14.61</geo:lat>
        <geo:long>-92.84</geo:long>
    </item>
</channel>
</rss>
*Containing 15 items.
'''

# Download data as lxml
ssn_url = 'http://www.ssn.unam.mx/rss/ultimos-sismos.xml'
delay = 180 #3 sec
while True:
    print('Rquesting...')
    page = requests.get(ssn_url)
    xml_content = soup(page.content,features='xml')
    print('Got Response')
    # Now we need to get the date and time to know the latest reported item
    items = xml_content.find_all('item')

    # First item is the most recent, we need to know the date to make sure
    # we are not overwriting existing entries
    latest_read = items[0].find('description').text
    # 'Fecha:2020-10-04 18:06:42 (Hora de México)Lat/Lon: 16.59/-98.84Profundidad: 5.0 km  ]]>'
    date_and_time = latest_read[10:29]
    print('Latest read date:',date_and_time)
    # '2020-10-04 18:06:42'
    downloaded_file_date = datetime.datetime.strptime(date_and_time, '%Y-%m-%d %H:%M:%S')
    # datetime.datetime(2020, 10, 4, 18, 6, 42)
    # Now we can compare the downloaded file date to the other files

    file_dir ='data/sismos/'
    entries = os.listdir(file_dir)
    if len(entries) == 0:
        with open(file_dir
        +downloaded_file_date.strftime('%Y-%m-%d')
        +'.xml','w') as f:
            f.write(xml_content.prettify())
            f.close()
    else:
        # Find the latest file, the file's name is the date
        entries.sort(reverse=True)


        # Open the file to explore its content
        with open(file_dir+entries[0],'r') as f:
            existing_file = f.read()
            f.close()
            # Same procedure as the begenning
            content = soup(existing_file,features='xml')
            # Create a new date obj to compare
            recent_file_date = content.find('item').description.text[14:33]
            print('recent_file_date:',recent_file_date)
            recent_file_date = datetime.datetime.strptime(recent_file_date, '%Y-%m-%d %H:%M:%S')

            if downloaded_file_date.date() > recent_file_date.date():
                # create a new file
                with open(file_dir
                +downloaded_file_date.strftime('%Y-%m-%d')
                +'.xml','w') as f:
                    f.write(xml_content.prettify())
                    f.close()
            elif downloaded_file_date.time() > recent_file_date.time():
                # update the existing items in the file
                # First we save all old items dates in a list
                old_items = content.find_all('item')
                old_items_dates = [o.description.text[14:33] for o in old_items]
                # Now we get a list of all new items that were not in the file
                new_items = [i for i in items if i.description.text[10:29] not in old_items_dates]
                # To keep the same file structure, the list must be sorted from last
                # recent to most recent, so it's easier to add to the list
                new_items.sort(key=lambda i:i.description.text[10:29])
                # Update the item list
                for ni in new_items:
                    old_items.insert(0,ni)
                # Create the parent tags to overwrite the file
                xml_tag = soup('<?xml version="1.0"?><rss version="2.0"\
                 xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"><channel>\
                 <title>Reporte diario de sismos registrados por el SSN</title>\
                 <link>http://www.ssn.unam.mx</link>\
                 <description>Reporte de sismos en México</description>\
                 </channel></rss>',features='xml')
                # Insert the items in channel tag
                for i in old_items:
                    xml_tag.channel.append(i)
                with open(file_dir+entries[0],'w') as f:
                    f.write(xml_tag.prettify())
                    f.close()
    print('Sleeping...')
    time.sleep(delay)
