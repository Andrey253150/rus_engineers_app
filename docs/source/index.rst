.. Russian Engineers documentation master file, created by
   sphinx-quickstart on Mon Feb  3 22:03:11 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Добро пожаловать в документацию Russian Engineers!
====================================================

.. toctree::
   :maxdepth: 4
   :caption: Содержание:

   modules

.. .. automodule:: app
..    :members:
..    :undoc-members:
..    :show-inheritance:
..    :noindex:


Структура проекта
-----------------

.. important::

    Обратите внимание, что папки `__pycache__/, venv/, .git/, .DS_store/` исключены из дерева структуры проекта.


.. literalinclude:: ../project_structure.txt
   :language: text


Ключевые диаграммы приложения
------------------------------

.. container:: image-with-text

   .. rst-class:: spaced-image

   .. figure:: ./_static/images/objects_dependencies_russian-engineers.png
      :alt: Компоненты приложения
      :width: 200%
      :align: center

      Компоненты приложения (сделана с помощью pydeps)


   .. rst-class:: spaced-image

   .. figure:: ./_static/images/packages_russian-engineers.png
      :alt: Пакеты и модули приложения
      :width: 200%
      :align: center

      Пакеты и модули приложения (сделана с помощью pyreverse)


   .. rst-class:: spaced-image

   .. figure:: ./_static/images/classes_russian-engineers.png
      :alt: Основные классы приложения
      :width: 120%
      :align: center

      Основные классы приложения (сделана с помощью pyreverse)


   .. rst-class:: spaced-image

   .. figure:: ./_static/images/erd_russian-engineers.png
      :alt: ER-диаграмма приложения
      :width: 120%
      :align: center

      ER-диаграмма приложения (сделана с помощью eralchemy)
   
   Текст для контейнера 


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`


