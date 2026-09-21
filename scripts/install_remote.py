"""Install the plugin into the dedicated demo container only."""
import json,subprocess,pathlib
root=pathlib.Path('/home/aime/atelier-tryon')
def run(*args):
 r=subprocess.run(args)
 if r.returncode: raise SystemExit('Installation step failed (arguments redacted).')
a=json.loads((root/'admin.json').read_text())
run('docker','exec','atelier-shopware','php','bin/console','user:create',a['username'],'--admin','--email=atelier@example.invalid','--password='+a['password'],'-n')
run('docker','exec','atelier-shopware','php','bin/console','sales-channel:update:domain','http://192.168.1.120:8090','--previous-domain=http://localhost')
run('docker','exec','-u','root','atelier-shopware','mkdir','-p','/var/www/html/custom/plugins/AtelierYou')
run('docker','cp',str(root/'repo/shopware/AtelierYou')+'/.','atelier-shopware:/var/www/html/custom/plugins/AtelierYou/')
run('docker','exec','atelier-shopware','php','bin/console','plugin:refresh')
run('docker','exec','atelier-shopware','php','bin/console','plugin:install','--activate','AtelierYou')
run('docker','exec','atelier-shopware','php','bin/console','assets:install')
run('docker','exec','atelier-shopware','php','bin/console','cache:clear')
config=root/'atelier-proxy.conf'
config.write_text('ProxyPass /tryon/ http://192.168.1.120:8091/tryon/\nProxyPassReverse /tryon/ http://192.168.1.120:8091/tryon/\n')
run('docker','cp',str(config),'atelier-shopware:/etc/apache2/conf-available/atelier-proxy.conf')
run('docker','exec','-u','root','atelier-shopware','a2enmod','proxy','proxy_http')
run('docker','exec','-u','root','atelier-shopware','a2enconf','atelier-proxy')
run('docker','exec','-u','root','atelier-shopware','apachectl','-k','graceful')
