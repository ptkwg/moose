"""
Module for defining the default Lexer objects that plugin to base.Reader objects.
"""
import collections
import logging
import traceback
import types
import re

import MooseDocs
from MooseDocs import common
from MooseDocs.tree import tokens
from MooseDocs.common import exceptions

LOG = logging.getLogger(__name__)

class Pattern(object):
    """
    Object for storing token creation items.

    Inputs:
         name[str]: The name of the tokenization component (e.g., Heading).
         regex: Compiled python re for creating token.
         function: The function to call when a match occurs (components.Component.__call__).
    """
    def __init__(self, name, regex, function):

        # Perform input type checking
        common.check_type('name', name, str)
        common.check_type('regex', regex, type(re.compile('')))
        common.check_type('function', function, types.FunctionType)

        self.name = name
        self.regex = regex
        self.function = function

class Grammer(object):
    """
    Defines a generic Grammer that contains the Token objects necessary to build an
    abstract syntax tree (AST). This class defines the order that the tokens will be
    applied to the Lexer object and the associated regular expression that define the
    text associated with the Token object.
    """

    #: Container for information required for creating a Token object.
   # Pattern = collections.namedtuple('Pattern', 'name regex function')

    def __init__(self):
        self.__patterns = common.Storage(Pattern)

    def add(self, name, regex, function, location='_end'):
        """
        Method for adding a Token definition to the Grammer object.

        Inputs:
            name[str]: The name of the grammer definition, this is utilized for
                       ordering of the definitions.
            regex[re]: A compiled re object that defines what text the token should
                       be associated.
            function[function]: A function that accepts a regex match object as input and
                                returns a token object.
            location[int or str]:  (Optional) In the case of an int type, this is an
                                   index indicating the location in the list of definitions
                                   to insert. In the case of a str type the following syntax
                                   is support to insert definitions relative to other
                                   definitions.
                                        '_begin': Insert the new definition at the beginning
                                                  of the list of definitions, this is the same
                                                  as using an index of 0.
                                        '_end': Append the new definition at the end of the list
                                                of definitions (this is the default).
                                        '<foo': Insert the new definition before the definition
                                                named 'foo'.
                                        '>foo': Insert the new definition after the definition
                                                named 'foo'.
        """
        # Add the supplied information to the storage.
        common.check_type('location', location, (int, str))
        self.__patterns.add(name, Pattern(name, regex, function), location)

    def __contains__(self, key):
        """
        Return True if the key is contained in the defined patterns.
        """
        return key in self.__patterns

    def __getitem__(self, key):
        """
        Return the pattern for a given key.
        """
        return self.__patterns[key]

    def __iter__(self):
        """
        Provide iterator access to the patterns.
        """
        for obj in self.__patterns:
            yield obj

    def __str__(self):
        out = []
        for obj in self.__patterns:
            out.append(str(obj))
        return 'Grammer:\n' + ', '.join(out)

class LexerInformation(object):
    """
    Lexer meta data object to keep track of necessary information for strong error reporting.

    Inputs:
        match[re.Match]: The regex match object from which a Token object is to be created.
        pattern[Grammer.Pattern]: Grammer pattern definition, see Grammer.py.
        line[int]: Current line number in supplied parsed text.
    """
    def __init__(self, match=None, pattern=None, line=None):
        self.__match = dict()
        self.__pattern = pattern.name
        self.__line = line

        self.__match[0] = match.group(0)
        for i, group in enumerate(match.groups()):
            self.__match[i+1] = group
        for key, value in match.groupdict().iteritems():
            self.__match[key] = value

    @property
    def line(self):
        """
        Return the line number for the regex match.
        """
        return self.__line

    @property
    def pattern(self):
        """
        Return the Grammer.Pattern for the regex match.
        """
        return self.__pattern

    @property
    def match(self):
        """
        Return the re Match object.
        """
        return self.__match

    def __getitem__(self, value):
        """
        Return the regex group by number or name.

        Inputs:
            value[int|str]: The regex group index or name.
        """
        return self.__match[value]

    def get(self, name, default=None):
        """
        Return the group or the supplied default.
        """
        return self.__match.get(name, default)

    def keys(self):
        """
        List of named regex groups.
        """
        return self.__match.keys()

    def iteritems(self):
        """
        Iterate over the named groups.
        """
        for key, value in self.__match.iteritems():
            yield key, value

    def __contains__(self, value):
        """
        Check if a named group exists in the regex match.
        """
        return value in self.__match

    def __str__(self):
        """
        Return a reasonable string for debugging.
        """
        return 'line:{} match:{} pattern:{}'.format(self.__line, self.__match, self.__pattern)

class Lexer(object):
    """
    Simple regex base lexer.

    This provides a basic linear means to use regular expressions to tokenize text. The tokenize
    method starts with the complete text, loops through all the patterns (defined in Grammer
    object). When a match is found the function attached to the grammer is called. The text is then
    searched again starting at the end position of the last match.

    Generally, this object should not be used. It is designed to provide the general capability
    needed for the RecursiveLexer.
    """
    def __init__(self):
        pass

    def tokenize(self, parent, grammer, text, line=1):
        """
        Perform tokenization of the supplied text.

        Inputs:
            parent[tree.tokens]: The parent token to which the new token(s) should be attached.
            grammer[Grammer]: Object containing the grammer (defined by regexs) to search.
            text[unicode]: The text to tokenize.
            line[int]: The line number to startwith, this allows for nested calls to begin with
                       the correct line.

        NOTE: If the functions attached to the Grammer object raise a TokenizeException it will
              be caught by this object and converted into an Exception token. This allows for
              the entire text to be tokenized and have the errors report upon completion. The
              TokenizeException also contains information about the error, via a LexerInformation
              object to improve error reports.
        """
        common.check_type('text', text, unicode, exc=exceptions.TokenizeException)

        n = len(text)
        pos = 0
        while pos < n:
            match = None
            for pattern in grammer:
                match = pattern.regex.match(text, pos)
                if match:
                    info = LexerInformation(match, pattern, line)
                    try:
                        obj = self.buildObject(parent, pattern, info)
                    except Exception as e: #pylint: disable=broad-except
                        obj = tokens.ExceptionToken(parent,
                                                    info=info,
                                                    message=e.message,
                                                    traceback=traceback.format_exc())
                    if obj is not None:
                        obj.info = info #TODO: set ptype on base Token, change to info
                        line += match.group(0).count('\n')
                        pos = match.end()
                        break
                    else:
                        continue

            if match is None:
                break

        # Produce Exception token if text remains that was not matched
        if pos < n:
            msg = u'Unprocessed text exists:\n{}'.format(common.box(text[pos:], line=line))
            LOG.error(msg)

    def buildObject(self, parent, pattern, info): #pylint: disable=no-self-use
        """
        Return a token object for the given lexer information.
        """
        obj = pattern.function(info, parent)
        if MooseDocs.LOG_LEVEL == logging.DEBUG:
            common.check_type('obj', obj, (tokens.Token, type(None)),
                              exc=exceptions.TokenizeException)
        return obj

class RecursiveLexer(Lexer):
    """
    A lexer that accepts mulitple grammers and automatically processes the content recusively
    base on regex group names.

    Inputs:
        base[str]: The starting (or base) grammer group name to begin tokenization.
        *args: Additional grammer group names that will be included.

    Example:
       Given a regular expression such as '(?P<foo>.*>)'. If this object has a 'grammer' object
       defined with the name 'foo', tokenize will automatically be called with the content
       of the 'foo' group using the 'foo' grammer.
    """
    def __init__(self, base, *args):
        Lexer.__init__(self)
        self._grammers = collections.OrderedDict()
        self._grammers[base] = Grammer()
        for name in args:
            self._grammers[name] = Grammer()

    def grammer(self, group=None):
        """
        Return the Grammer object by group name.

        Inputs:
            group[str]: The name of the grammer group to return, if not given the base is returned.
        """
        if group is None:
            group = self._grammers.keys()[0]
        return self._grammers[group]

    def grammers(self):
        """
        Return the complete dictionary of Grammer objects.
        """
        return self._grammers

    def add(self, group, *args):
        """
        Append a component to the provided group.
        """
        self.grammer(group).add(*args)

    def buildObject(self, parent, pattern, info):
        """
        Override the Lexer.buildObject method to recursively tokenize base on group names.
        """
        if MooseDocs.LOG_LEVEL == logging.DEBUG:
            common.check_type('parent', parent, tokens.Token, exc=exceptions.TokenizeException)
            common.check_type('info', info, LexerInformation, exc=exceptions.TokenizeException)

        obj = super(RecursiveLexer, self).buildObject(parent, pattern, info)

        if (obj is not None) and (obj is not parent) and obj.recursive:
            for key, grammer in self._grammers.iteritems():
                if key in info.keys():
                    text = info[key]
                    if text is not None:
                        self.tokenize(obj, grammer, text, info.line)
        return obj
