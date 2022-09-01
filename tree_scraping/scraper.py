from enum import Enum
from select import select 
from time import sleep
from typing import Tuple, Union, List, Dict
from functools import wraps
import inspect

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
import chromedriver_autoinstaller as chromedriver


Selector = str
SelectorAttr = Union[Selector, Tuple[Selector, str]]
SelectorDict = dict[str, SelectorAttr]

ExtractResult = Union[any, dict[str, any]]


class Scraper:
    def __init__(self) -> None:
        chromedriver.install()
        self.__driver = webdriver.Chrome()
        self.__extract_results: List[ExtractResult] = []
        self.__function_queue: List[Tuple] = []
    

    def chain_decorator(func):

        @wraps(func)
        def wrapper(self, *args):
                arguments = {}
                names = list(inspect.signature(func).parameters.keys())[1:]
                
                for name, value in zip(names, args):
                    arguments[name] = value
                
                if 'foreach_visited_page' in arguments and arguments['foreach_visited_page']:
                    self.__function_queue.append((func.__name__, arguments))
                    return self

                if len(self.__function_queue) == 0:
                    return func(self, *args)

                self.__function_queue.append((func.__name__, arguments))
                self.__empty_function_queue()
                return self
            
        return wrapper
    

    def __do_call(self, call: Tuple[str, Dict[str, any]], link: any) -> None:
        name, args = call

        if name == 'click':
            link.click()
        elif name == 'navigate':
            args['url'] = link
            self.navigate.__wrapped__(self, *args)
        else:
            func = getattr(self, call[0])
            args = call[1].values()

            func.__wrapped__(self, *args)


    def __empty_function_queue(self) -> None:

        def get_function_links(call: Tuple[str, Dict[str, any]]) -> List[any]:
            name, parameters = call

            if name == 'click':
                return self.__get_element(parameters['selector'], True)
            elif name == 'navigate':
                url = parameters['url']
                return url if isinstance(url, list) else [url]
        

        root_url = self.__driver.current_url
        queue_size = len(self.__function_queue)
        last_call = self.__function_queue[-1]

        if last_call[0] != 'navigate' and last_call[0] != 'click':
            queue_size -= 1

        visited_links_counters = [0] * queue_size
        links_numbers = [0] * queue_size

        while True:

            for i in range(queue_size):

                link_to_click_on = None
                call = self.__function_queue[i]

                links = get_function_links(call)
                links_numbers[i] = len(links)
                link_to_click_on = links[visited_links_counters[i]]

                if visited_links_counters[i] == links_numbers[i] - 1 and i > 0:
                    visited_links_counters[i] = 0
                    visited_links_counters[i - 1] += 1
                elif i == queue_size - 1:
                    visited_links_counters[-1] += 1
                
                self.__do_call(call, link_to_click_on)
            
            if last_call[0] != 'navigate' and last_call[0] != 'click':
                self.__do_call(last_call, None)

            self.__driver.get(root_url)            

            if visited_links_counters[0] == links_numbers[0]:
                break
        
        self.__function_queue = []


    def __get_element(self, selector_attr: SelectorAttr, all: bool = False):
        selector_fun_name = 'find_elements_by_xpath' if all else 'find_element_by_xpath'    
        selector_fun = getattr(self.__driver, selector_fun_name)
        callback = None
        elements = None

        if isinstance(selector_attr, tuple):
            elements = selector_fun(selector_attr[0])
            callback = lambda el: el.get_attribute(selector_attr[1])
        else:
            elements = selector_fun(selector_attr)
            callback = lambda el: el
        
        if all:
            return [callback(element) for element in elements]
        return callback(elements)
    

    @chain_decorator
    def navigate(self, url: Union[str, List[str]], foreach_visited_page: bool = False):
        if isinstance(url, list):
            for u in url:
                self.__driver.get(u)
        else:
            self.__driver.get(url)

        return self


    @chain_decorator
    def click(self, selector: Selector, delay: int = 0, foreach_visited_page: bool = False):
        elements = self.__get_element(selector, True)

        for element in elements:
            element.click()
            sleep(delay)
        
        return self
    

    @chain_decorator
    def write(self, selector: Selector, text: str, delay: int = 0):
        elements = self.__get_element(selector, True)

        for element in elements:
            element.send_keys(text)
            sleep(delay)

        return self


    @chain_decorator
    def find(self, selector: Union[SelectorAttr, SelectorDict]):
        if isinstance(selector, dict):
            extract_result = {}

            for key in selector.keys():
                extract_result[key] = self.__get_element((selector[key][0], selector[key][1]))

            self.__extract_results.append(extract_result)

            return self

        self.__extract_results.append(self.__get_element((selector, 'innerHTML')))

        return self


    @chain_decorator
    def extract(self) -> List[ExtractResult]:
        if len(self.__extract_results) == 1:
            return self.__extract_results[0]
        return self.__extract_results