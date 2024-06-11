from setuptools import setup, find_packages

setup(
    name='CarbonAbatementOfBess',
    version='0.1',
    description='Deep Reinforcement Learning to Enhance Carbon Abatement Potential of Battery Energy Storage Systems',
    author='Christopher Saad',
    author_email='christopher.saad22@imperial.ac.uk',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'futures',
        'requests',
        'httplib2',
        'pytest',
        'openpyxl',
        'torch',
        'wandb',
        'stable_baselines3',
        'gymnasium',
        'tensorboard',
        'seaborn'
    ],
)
