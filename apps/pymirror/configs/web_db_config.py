from dataclasses import dataclass, field

@dataclass
class WebDbConfig:
    cycle_time: str = "60s"
    total: str = "{{payload.totalResults}}"
    max: str = "100"
    display: dict = field(default_factory=dict)

    # header: str = "{{_n_}}/{{payload.totalResults}}: {{payload.articles[_n_].title}}"
    # body: str = "{{payload.articles[_n_].description}}"
    # footer: str = "{{payload.articles[_n_].source.name}} @ {{ payload.articles[_n_].publishedAt.split('T')[0] }} -  {{ payload.articles[_n_].publishedAt.split('T')[1].replace('Z', '') }}"
