
const isElectron = window.location.protocol === 'file:';

const API_URL = isElectron
  ? 'http://127.0.0.1:8000/api/v1'
  : '/api/v1';
  

export interface Translation {
  external_id: string
  title: string
}

export interface MovieEpisode {
  id: number
  external_id: string
  translation: Translation
  season: number
  episode: number
  stream: string | null
}

export interface Movie {
  id: number
  external_id: string
  title: string
  description: string
  poster: string
  fill_title: string
  fill_description: string
  fill_poster: string
  url: string
  source: string
  episodes: MovieEpisode[]
}

export interface History {
  movie: Movie
  updated_at: string
}

export interface SourcesResponse  {
  sources: string[]
}

export interface MoviesResponse {
  movies: Movie[]
}

export interface HistoryResponse {
  history: History[]
}


export async function getSources(): Promise<SourcesResponse> {
  let res = undefined;
  
  try {
    res = await fetch(`${API_URL}/sources/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    throw new Error("No connection");
  }

  const data: SourcesResponse = await res.json();
  return data;
}

export async function fill(movie: Movie): Promise<Movie> {
  let res = undefined;
  
  try {
    res = await fetch(`${API_URL}/movie/${movie.id}/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    throw new Error("No connection");
  }

  const data: Movie = await res.json();
  return data;
}

export async function search(query: string, sources: string[], signal?: AbortSignal): Promise<MoviesResponse> {
  let res = undefined;
  
  try {
    const params = new URLSearchParams();
    params.append("query", query);

    sources.forEach(source => params.append("source", source));
    
    res = await fetch(`${API_URL}/movies/search?${params.toString()}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal
    });
  } catch {
    const data: MoviesResponse = { movies: [] }

    return data;
  }

  const data: MoviesResponse = await res.json();
  return data;
}

export async function getHistory(): Promise<HistoryResponse> {
  let res = undefined;
  
  try {
    res = await fetch(`${API_URL}/history`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    const data: HistoryResponse = { history: [] }

    return data;
  }

  const data: HistoryResponse = await res.json();
  return data;
}

export async function fillMovieEpisode(episode: MovieEpisode): Promise<MovieEpisode> {
  let res = undefined;
  
  try {
    res = await fetch(`${API_URL}/episode/${episode.id}/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    throw new Error("No connection");
  }

  const data: MovieEpisode = await res.json();
  return data;
}