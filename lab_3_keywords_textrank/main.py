"""
Lab 3
Extract keywords based on TextRank algorithm
"""
from typing import Optional, Union
from itertools import combinations, repeat, filterfalse
import re
from pathlib import Path
import csv
from lab_1_keywords_tfidf.main import (
    calculate_frequencies,
    calculate_tf,
    calculate_tfidf,
    get_top_n
)
from lab_2_keywords_cooccurrence.main import (
    extract_phrases,
    extract_candidate_keyword_phrases,
    calculate_frequencies_for_content_words,
    calculate_word_degrees,
    calculate_word_scores
)


class TextPreprocessor:
    """
    A class to preprocess raw text

    ...

    Attributes
    ----------
    _stop_words: tuple[str, ...]
        insignificant words to remove from tokens
    _punctuation: tuple[str, ...]
        punctuation symbols to remove during text cleaning

    Methods
    -------
    _clean_and_tokenize(text: str) -> tuple[str, ...]:
        Removes punctuation, casts to lowercase, splits into tokens.
    _remove_stop_words(tokens: tuple[str, ...] -> tuple[str, ...]:
        Filters tokens, removing stop words
    preprocess_text(text: str) -> tuple[str, ...]:
        Produces filtered clean lowercase tokens from raw text
    """
    # Step 1.1
    def __init__(self, stop_words: tuple[str, ...], punctuation: tuple[str, ...]) -> None:
        """
        Constructs all the necessary attributes for the text preprocessor object

        Parameters
        ----------
            stop_words : tuple[str, ...]
                insignificant words to remove from tokens
            punctuation : tuple[str, ...]
                punctuation symbols to remove during text cleaning
        """
        self._stop_words, self._punctuation = stop_words, punctuation

    # Step 1.2
    def _clean_and_tokenize(self, text: str) -> tuple[str, ...]:
        """
        Removes punctuation, casts to lowercase, splits into tokens.

        Parameters
        ----------
            text : str
                raw text

        Returns
        -------
            tuple[str, ...]
                clean lowercase tokens
        """
        if self._punctuation:
            expression = re.compile('[' + ''.join(list(self._punctuation)) + ']')
            return tuple(re.sub(expression, '', text).lower().split())
        return tuple(text.lower().split())

    # Step 1.3
    def _remove_stop_words(self, tokens: tuple[str, ...]) -> tuple[str, ...]:
        """
        Filters tokens, removing stop words

        Parameters
        ----------
            tokens : tuple[str, ...]
                tokens containing stop-words

        Returns
        -------
            tuple[str, ...]
                tokens without stop-words
        """
        return tuple(token for token in tokens if token not in self._stop_words)

    # Step 1.4
    def preprocess_text(self, text: str) -> tuple[str, ...]:
        """
        Produces filtered clean lowercase tokens from raw text

        Parameters
        ----------
            text : str
                raw text

        Returns
        -------
            tuple[str, ...]
                clean lowercase tokens with no stop-words
        """
        return self._remove_stop_words(self._clean_and_tokenize(text))


class TextEncoder:
    """
    A class to encode string sequence into matching integer sequence

    ...

    Attributes
    ----------
    _word2id: dict[str, int]
        maps words to integers
    _id2word: dict[int, str]
        maps integers to words

    Methods
    -------
     _learn_indices(self, tokens: tuple[str, ...]) -> None:
        Fills attributes mapping words and integer equivalents to each other
    encode(self, tokens: tuple[str, ...]) -> Optional[tuple[int, ...]]:
        Encodes input sequence of string tokens to sequence of integer tokens
    decode(self, encoded_tokens: tuple[int, ...]) -> Optional[tuple[str, ...]]:
        Decodes input sequence of integer tokens to sequence of string tokens
    """

    # Step 2.1
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the text encoder object
        """
        self._word2id, self._id2word = {}, {}

    # Step 2.2
    def _learn_indices(self, tokens: tuple[str, ...]) -> None:
        """
        Fills attributes mapping words and integer equivalents to each other

        Parameters
        ----------
            tokens : tuple[str, ...]
                sequence of string tokens
        """
        for count, token in enumerate(tokens):
            self._word2id[token] = 1000 + count
            self._id2word[self._word2id[token]] = token

    # Step 2.3
    def encode(self, tokens: tuple[str, ...]) -> Optional[tuple[int, ...]]:
        """
        Encodes input sequence of string tokens to sequence of integer tokens

        Parameters
        ----------
            tokens : tuple[str, ...]
                sequence of string tokens

        Returns
        -------
            tuple[int, ...]
                sequence of integer tokens

        In case of empty tokens input data, None is returned
        """
        self._learn_indices(tokens)
        return None if not tokens else tuple(self._word2id[token] for token in tokens)

    # Step 2.4
    def decode(self, encoded_tokens: tuple[int, ...]) -> Optional[tuple[str, ...]]:
        """
        Decodes input sequence of integer tokens to sequence of string tokens

        Parameters
        ----------
            encoded_tokens : tuple[int, ...]
                sequence of integer tokens

        Returns
        -------
            tuple[str, ...]
                sequence of string tokens

        In case of out-of-dictionary input data, None is returned
        """
        try:
            return tuple(self._id2word[number] for number in encoded_tokens)
        except KeyError:
            return None


# Step 3
def extract_pairs(tokens: tuple[int, ...], window_length: int) -> Optional[tuple[tuple[int, ...], ...]]:
    """
    Retrieves all pairs of co-occurring words in the token sequence

    Parameters
    ----------
        tokens : tuple[int, ...]
            sequence of tokens
        window_length: int
            maximum distance between co-occurring tokens: tokens are considered co-occurring
            if they appear in the same window of this length

    Returns
    -------
        tuple[tuple[int, ...], ...]
            pairs of co-occurring tokens

    In case of corrupt input data, None is returned:
    tokens must not be empty, window lengths must be integer, window lengths cannot be less than 2.
    """
    if not tokens or (not isinstance(window_length, int) or isinstance(window_length, bool)) or window_length < 2:
        return None
    pairs = []
    for index in range(len(tokens[:-window_length])):
        for pair in combinations(tokens[index:index + window_length], 2):
            if not pair[0] == pair[1] and pair not in pairs and (pair[1], pair[0]) not in pairs:
                pairs.append(pair)
    return tuple(pairs)


class AdjacencyMatrixGraph:
    """
    A class to represent graph as matrix of adjacency

    ...

    Attributes
    ----------
    _matrix: list[list[int]]
        stores information about vertices interrelation
    _positions: dict[int, list[int]]
        stores information about positions in text

    Methods
    -------
     get_vertices(self) -> tuple[int, ...]:
        Returns a sequence of all vertices present in the graph
     add_edge(self, vertex1: int, vertex2: int) -> int:
        Adds or overwrites an edge in the graph between the specified vertices
     is_incidental(self, vertex1: int, vertex2: int) -> int:
        Retrieves information about whether the two vertices are incidental
     calculate_inout_score(self, vertex: int) -> int:
        Retrieves a number of incidental vertices to a specified vertex
    fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        Updates graph instance with vertices and edges extracted from tokenized text
    fill_positions(self, tokens: tuple[int, ...]) -> None:
        Saves information on all positions of each vertex in the token sequence
    calculate_position_weights(self) -> None:
        Computes position weights for all tokens in text
    get_position_weights(self) -> dict[int, float]:
        Retrieves position weights for all vertices in the graph
    """

    _matrix: list[list[int]]
    _positions: dict[int, list[int]]
    _position_weights: dict[int, float]

    # Step 4.1
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the adjacency matrix graph object
        """
        self._matrix, self._positions, self._position_weights = [[]], {}, {}

    # Step 4.2
    def add_edge(self, vertex1: int, vertex2: int) -> int:
        """
        Adds or overwrites an edge in the graph between the specified vertices

        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the added edge
            vertex2 : int
                the second vertex incidental to the added edge

        Returns
        -------
            int
                0 if edge was added successfully, otherwise -1

        In case of vertex1 being equal to vertex2, -1 is returned as loops are prohibited
        """
        if vertex1 == vertex2:
            return -1
        for vertex in vertex1, vertex2:
            if vertex not in self._matrix[0]:
                self._matrix.append([vertex] + list(repeat(0, len(self._matrix[0]))))
                self._matrix[0].append(vertex)
                for i in self._matrix[1:]:
                    i.append(0)
        index1, index2 = self._matrix[0].index(vertex1) + 1, self._matrix[0].index(vertex2) + 1
        self._matrix[index1][index2] = self._matrix[index2][index1] = 1
        return 0

    # Step 4.3
    def is_incidental(self, vertex1: int, vertex2: int) -> int:
        """
        Retrieves information about whether the two vertices are incidental

        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the edge sought
            vertex2 : int
                the second vertex incidental to the edge sought

        Returns
        -------
            Optional[int]
                1 if vertices are incidental, otherwise 0

        If either of vertices is not present in the graph, -1 is returned
        """
        if vertex1 not in self._matrix[0] or vertex2 not in self._matrix[0]:
            return -1
        return self._matrix[self._matrix[0].index(vertex1) + 1][self._matrix[0].index(vertex2) + 1]

    # Step 4.4
    def get_vertices(self) -> tuple[int, ...]:
        """
        Returns a sequence of all vertices present in the graph

        Returns
        -------
            tuple[int, ...]
                a sequence of vertices present in the graph
        """
        return tuple(self._matrix[0])

    # Step 4.5
    def calculate_inout_score(self, vertex: int) -> int:
        """
        Retrieves a number of incidental vertices to a specified vertex

        Parameters
        ----------
            vertex : int
                a vertex to calculate inout score for

        Returns
        -------
            int
                number of incidental vertices

        If vertex is not present in the graph, -1 is returned
        """
        return -1 if vertex not in self._matrix[0] else sum(self._matrix[self._matrix[0].index(vertex) + 1][1:])

    # Step 4.6
    def fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        """
        Updates graph instance with vertices and edges extracted from tokenized text
        Parameters
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
            window_length: int
                maximum distance between co-occurring tokens: tokens are considered co-occurring
                if they appear in the same window of this length
        """
        for pair in extract_pairs(tokens, window_length):
            self.add_edge(pair[0], pair[1])

    # Step 8.2
    def fill_positions(self, tokens: tuple[int, ...]) -> None:
        """
        Saves information about all positions of each vertex in the token sequence
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
        """
        for count, item in enumerate(tokens):
            self._positions[item] = self._positions.get(item, []) + [count + 1]

    # Step 8.3
    def calculate_position_weights(self) -> None:
        """
        Computes position weights for all tokens in text
        """
        non_normalized = {token: sum(1 / position for position in self._positions[token]) for token in self._positions}
        non_normalized_sum = sum(non_normalized.values())
        self._position_weights = {i: non_normalized[i] / non_normalized_sum for i in non_normalized}

    # Step 8.4
    def get_position_weights(self) -> dict[int, float]:
        """
        Retrieves position weights for all vertices in the graph

        Returns
        -------
            dict[int, float]
                position weights for all vertices in the graph
        """
        return self._position_weights


class EdgeListGraph:
    """
    A class to represent graph as a list of edges

    ...

    Attributes
    ----------
    _edges: dict[int, list[int]]
        stores information about vertices interrelation

    Methods
    -------
     get_vertices(self) -> tuple[int, ...]:
        Returns a sequence of all vertices present in the graph
     add_edge(self, vertex1: int, vertex2: int) -> int:
        Adds or overwrites an edge in the graph between the specified vertices
     is_incidental(self, vertex1: int, vertex2: int) -> int:
        Retrieves information about whether the two vertices are incidental
     calculate_inout_score(self, vertex: int) -> int:
        Retrieves a number of incidental vertices to a specified vertex
    fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        Updates graph instance with vertices and edges extracted from tokenized text
    fill_positions(self, tokens: tuple[int, ...]) -> None:
        Saves information on all positions of each vertex in the token sequence
    calculate_position_weights(self) -> None:
        Computes position weights for all tokens in text
    get_position_weights(self) -> dict[int, float]:
        Retrieves position weights for all vertices in the graph
    """

    # Step 7.1
    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the edge list graph object
        """
        self._edges, self._positions, self._position_weights = {}, {}, {}

    # Step 7.2
    def get_vertices(self) -> tuple[int, ...]:
        """
        Returns a sequence of all vertices present in the graph

        Returns
        -------
            tuple[int, ...]
                a sequence of vertices present in the graph
        """
        return tuple(self._edges.keys())

    # Step 7.2
    def add_edge(self, vertex1: int, vertex2: int) -> int:
        """
        Adds or overwrites an edge in the graph between the specified vertices

        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the added edge
            vertex2 : int
                the second vertex incidental to the added edge

        Returns
        -------
            int
                0 if edge was added successfully, otherwise -1

        In case of vertex1 being equal to vertex2, -1 is returned as loops are prohibited
        """
        if vertex1 == vertex2:
            return -1
        if vertex1 not in self._edges.get(vertex2, []):
            self._edges[vertex1] = self._edges.get(vertex1, []) + [vertex2]
            self._edges[vertex2] = self._edges.get(vertex2, []) + [vertex1]
        return 0

    # Step 7.2
    def is_incidental(self, vertex1: int, vertex2: int) -> int:
        """
        Retrieves information about whether the two vertices are incidental

        Parameters
        ----------
            vertex1 : int
                the first vertex incidental to the edge sought
            vertex2 : int
                the second vertex incidental to the edge sought

        Returns
        -------
            Optional[int]
                1 if vertices are incidental, otherwise 0

        If either of vertices is not present in the graph, -1 is returned
        """
        if vertex1 not in self._edges or vertex2 not in self._edges:
            return -1
        return 1 if vertex1 in self._edges[vertex2] else 0

    # Step 7.2
    def calculate_inout_score(self, vertex: int) -> int:
        """
        Retrieves a number of incidental vertices to a specified vertex

        Parameters
        ----------
            vertex : int
                a vertex to calculate inout score for

        Returns
        -------
            int
                number of incidental vertices

        If vertex is not present in the graph, -1 is returned
        """
        return len(self._edges[vertex]) if vertex in self._edges else -1

    # Step 7.2
    def fill_from_tokens(self, tokens: tuple[int, ...], window_length: int) -> None:
        """
        Updates graph instance with vertices and edges extracted from tokenized text
        Parameters
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
            window_length: int
                maximum distance between co-occurring tokens: tokens are considered co-occurring
                if they appear in the same window of this length
        """
        for pair in extract_pairs(tokens, window_length):
            self.add_edge(pair[0], pair[1])

    # Step 8.2
    def fill_positions(self, tokens: tuple[int, ...]) -> None:
        """
        Saves information on all positions of each vertex in the token sequence
        ----------
            tokens : tuple[int, ...]
                sequence of tokens
        """
        for count, item in enumerate(tokens):
            self._positions[item] = self._positions.get(item, []) + [count + 1]

    # Step 8.3
    def calculate_position_weights(self) -> None:
        """
        Computes position weights for all tokens in text
        """
        non_normalized = {token: sum(1 / position for position in self._positions[token]) for token in self._positions}
        non_normalized_sum = sum(non_normalized.values())
        self._position_weights = {i: non_normalized[i] / non_normalized_sum for i in non_normalized}

    # Step 8.4
    def get_position_weights(self) -> dict[int, float]:
        """
        Retrieves position weights for all vertices in the graph

        Returns
        -------
            dict[int, float]
                position weights for all vertices in the graph
        """
        return self._position_weights


class VanillaTextRank:
    """
    Basic TextRank implementation

    ...

    Attributes
    ----------
    _graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
        a graph representing the text
    _damping_factor: float
         probability of jumping from a given vertex to another random vertex
         in the graph during vertices scores calculation
    _convergence_threshold: float
        maximal acceptable difference between the vertices scores in two consequent iteration
    _max_iter: int
        maximal number of iterations to perform
    _scores: dict[int, float]
        scores of significance for all vertices present in the graph


    Methods
    -------
     update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        Changes vertex significance score using algorithm-specific formula
     score_vertices(self) -> dict[int, float]:
        Iteratively computes significance scores for vertices
     get_scores(self) -> dict[int, float]:
        Retrieves importance scores of all tokens in the encoded text
     get_top_keywords(self, n_keywords: int) -> tuple[int, ...]:
        Retrieves top n most important tokens in the encoded text
     """

    _scores: dict[int, float]

    # Step 5.1
    def __init__(self, graph: Union[AdjacencyMatrixGraph, EdgeListGraph]) -> None:
        """
        Constructs all the necessary attributes for the text rank algorithm implementation

        Parameters
        ----------
        graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
            a graph representing the text
        """
        self._graph, self._scores = graph, {}
        self._damping_factor, self._convergence_threshold, self._max_iter = 0.85, 0.0001, 50

    # Step 5.2
    def update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        """
        Changes vertex significance score using algorithm-specific formula

        Parameters
        ----------
            vertex : int
                a vertex which significance score is updated
            incidental_vertices: list[int]
                vertices incidental to the scored one
            scores: dict[int, float]
                scores of all vertices in the graph
        """
        self._scores[vertex] = (1 - self._damping_factor) + self._damping_factor * sum(
            1 / abs(self._graph.calculate_inout_score(i)) * scores[i] for i in incidental_vertices)

    # Step 5.3
    def train(self) -> None:
        """
        Iteratively computes significance scores for vertices

        Returns
        -------
            dict[int, float]:
                scores for all vertices present in the graph
        """
        vertices = self._graph.get_vertices()
        for vertex in vertices:
            self._scores[vertex] = 1.0

        for _ in range(0, self._max_iter):
            prev_score = self._scores.copy()
            for scored_vertex in vertices:
                incidental_vertices = [vertex for vertex in vertices
                                       if self._graph.is_incidental(scored_vertex, vertex) == 1]
                self.update_vertex_score(scored_vertex, incidental_vertices, prev_score)
            abs_score_diff = [abs(i - j) for i, j in zip(prev_score.values(), self._scores.values())]
            if sum(abs_score_diff) <= self._convergence_threshold:
                break

    # Step 5.4
    def get_scores(self) -> dict[int, float]:
        """
        Retrieves importance scores of all tokens in the encoded text

        Returns
        -------
            dict[int, float]
                importance scores of all tokens in the encoded text
        """
        return self._scores

    # Step 5.5
    def get_top_keywords(self, n_keywords: int) -> tuple[int, ...]:
        """
        Retrieves top n most important tokens in the encoded text

        Returns
        -------
            tuple[int, ...]
                top n most important tokens in the encoded text
        """
        return tuple(sorted(self._scores, key=lambda word: self._scores[word], reverse=True)[:n_keywords])


class PositionBiasedTextRank(VanillaTextRank):
    """
    Advanced TextRank implementation: positions of tokens in text are taken into consideration

    ...

    Attributes
    ----------
    _graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
        a graph representing the text
    _damping_factor: float
         probability of jumping from a given vertex to another random vertex
         in the graph during vertices scores calculation
    _convergence_threshold: float
        maximal acceptable difference between the vertices scores in two consequent iteration
    _max_iter: int
        maximal number of iterations to perform
    _scores: dict[int, float]
        scores of significance for all vertices present in the graph
    _position_weights: dict[int, float]
        position weights for all tokens in the text


    Methods
    -------
     update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        Changes vertex significance score using algorithm-specific formula
     score_vertices(self) -> dict[int, float]:
        Iteratively computes significance scores for vertices
     get_scores(self) -> dict[int, float]:
        Retrieves importance scores of all tokens in the encoded text
     get_top_keywords(self, n_keywords: int) -> tuple[int, ...]:
        Retrieves top n most important tokens in the encoded text
    """

    # Step 9.1
    def __init__(self, graph: Union[AdjacencyMatrixGraph, EdgeListGraph]) -> None:
        """
        Constructs all the necessary attributes
        for the position-aware text rank algorithm implementation

        Attributes
        ----------
        graph: Union[AdjacencyMatrixGraph, EdgeListGraph]
            a graph representing the text
        """
        super().__init__(graph)
        self._position_weights = graph.get_position_weights()

    # Step 9.2
    def update_vertex_score(self, vertex: int, incidental_vertices: list[int], scores: dict[int, float]) -> None:
        """
        Changes vertex significance score using algorithm-specific formula

        Parameters
        ----------
            vertex : int
                a vertex which significance score is updated
            incidental_vertices: list[int]
                vertices incidental to the scored one
            scores: dict[int, float]
                scores of all vertices in the graph
        """
        self._scores[vertex] = (1 - self._damping_factor) * self._position_weights[vertex] + self._damping_factor * sum(
            1 / abs(self._graph.calculate_inout_score(j)) * scores[j] for j in incidental_vertices)


class TFIDFAdapter:
    def __init__(self, tokens: tuple[str, ...], idf: dict[str, float]) -> None:
        """
        No docstring yet
        """
        self._tokens, self._idf, self._scores = tokens, idf, {}

    def train(self) -> int:
        """
        No docstring yet
        """
        frequencies = calculate_frequencies(list(self._tokens))
        tf_dict = None
        if frequencies:
            tf_dict = calculate_tf(frequencies)
        if tf_dict:
            self._scores = calculate_tfidf(tf_dict, self._idf)
        return 0 if self._scores else -1

    def get_top_keywords(self, n_keywords: int) -> tuple[str, ...]:
        """
        No docstring yet
        """
        return tuple(get_top_n(self._scores, n_keywords))

    def get_scores(self) -> dict[str, float]:
        """
        No docstring yet (this thing's purpose is passing tests)
        """
        return self._scores


class RAKEAdapter:
    def __init__(self, text: str, stop_words: tuple[str, ...]) -> None:
        """
        No docstring yet
        """
        self._text, self._stop_words, self._scores = text, stop_words, {}

    def train(self) -> int:
        """
        No docstring yet
        """
        candidate_keyword_phrases, word_frequencies, word_degrees = repeat(None, 3)
        phrases = extract_phrases(self._text)
        if phrases and self._stop_words:
            candidate_keyword_phrases = extract_candidate_keyword_phrases(phrases, list(self._stop_words))
        if candidate_keyword_phrases:
            word_frequencies = calculate_frequencies_for_content_words(candidate_keyword_phrases)
        if candidate_keyword_phrases and word_frequencies:
            word_degrees = calculate_word_degrees(candidate_keyword_phrases, list(word_frequencies.keys()))
        if word_degrees and word_frequencies:
            self._scores = calculate_word_scores(word_degrees, word_frequencies)
        return 0 if self._scores else -1

    def get_top_keywords(self, n_keywords: int) -> tuple[str, ...]:
        """
        No docstring yet
        """
        return tuple(get_top_n(self._scores, n_keywords))

    def get_scores(self) -> dict[str, float]:
        """
        No docstring yet (this thing's purpose is passing tests)
        """
        return self._scores


class KeywordExtractionBenchmark:
    def __init__(self, stop_words: tuple[str, ...], punctuation: tuple[str, ...], idf: dict[str, float],
                 materials_path: Path) -> None:
        """
        No docstring yet
        """
        self.stop_words, self.punctuation, self.idf, self.materials_path = stop_words, punctuation, idf, materials_path
        self.themes = ('culture', 'business', 'crime', 'fashion', 'health', 'politics', 'science', 'sports', 'tech')
        self.report = {}

    def calculate_recall(self, predicted: tuple[str, ...], target: tuple[str, ...]) -> float:
        """
        No docstring yet
        """
        true_positive = len(tuple(filterfalse(lambda token: token in predicted, target)))
        false_negative = len(target) - true_positive
        return true_positive / (true_positive + false_negative)

    def run(self) -> Optional[dict[str, dict[str, float]]]:
        """
        No docstring yet
        """
        try:
            for name in 'TF-IDF', 'RAKE', 'VanillaTextRank', 'PositionBiasedTextRank':
                self.report[name] = {}
            preprocessor = TextPreprocessor(self.stop_words, self.punctuation)
            encoder = TextEncoder()
            project_root = Path(__file__).parent
            assets = project_root / 'assets'
            benchmark_materials = assets / 'benchmark_materials'
            for theme in range(len(self.themes)):
                target_text_path = benchmark_materials / (str(theme) + '_text.txt')
                file = open(target_text_path, 'r', encoding='utf-8')
                text = file.read()
                file.close()
                target_keyword_path = benchmark_materials / (str(theme) + '_keywords.txt')
                file = open(target_keyword_path, 'r', encoding='utf-8')
                keywords = tuple(file.read().split())
                file.close()

                tokens = preprocessor.preprocess_text(text)
                tokens_encoded = encoder.encode(tokens)
                graph = EdgeListGraph()
                graph.fill_from_tokens(tokens_encoded, 3)
                graph.fill_positions(tokens_encoded)
                graph.calculate_position_weights()

                tfidf = TFIDFAdapter(tokens, self.idf)
                rake = RAKEAdapter(text, self.stop_words)
                vanilla_text_rank = VanillaTextRank(graph)
                position_biased = PositionBiasedTextRank(graph)

                for algorithm in tfidf, rake, vanilla_text_rank, position_biased:
                    algorithm.train()

                predict_tfidf = tfidf.get_top_keywords(50)
                self.report['TF-IDF'][self.themes[theme]] = self.calculate_recall(predict_tfidf, keywords)
                predict_rake = rake.get_top_keywords(50)
                self.report['RAKE'][self.themes[theme]] = self.calculate_recall(predict_rake, keywords)
                predict_vanilla = encoder.decode(vanilla_text_rank.get_top_keywords(50))
                self.report['VanillaTextRank'][self.themes[theme]] = self.calculate_recall(predict_vanilla, keywords)
                predict_biased = encoder.decode(position_biased.get_top_keywords(50))
                self.report['PositionBiasedTextRank'][self.themes[theme]] = \
                    self.calculate_recall(predict_biased, keywords)
        except TypeError:
            return None
        return self.report

    def save_to_csv(self, path: Path) -> None:
        """
        No docstring yet
        """
        with open(path, 'w', newline='') as csv_file:
            report_writer = csv.writer(csv_file)
            report_writer.writerow(['name'] + list(self.themes))
            for algorithm in self.report:
                report_writer.writerow([algorithm] +
                                       [self.report[algorithm][theme] for theme in self.report[algorithm]])
