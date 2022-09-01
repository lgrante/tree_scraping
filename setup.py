from setuptools import find_packages, setup


setup(
        name='scraping_tree',
        packages=find_packages(include=['scraping_tree']),
        version='0.1.0',
        description='Scraping library that allows to easily combines several actions in only one call',
        author='Louis Grante',
        author_email='louisgrante@outlook.fr'
        license='MIT',
        install_requires=['selenium', 'chromedriver_autoinstaller']
        keywords=['webscraping', 'tree']
)
