# ADR-0004: PyPI 배포와 운영 분담

- 날짜: 2026-10-05
- 상태: 승인
- English summary: releases are published to PyPI by GitHub Actions when a `v*` tag is pushed (tests → version check → build → twine check → upload). The maintainer only handles what requires their identity: accounts, tokens, secrets. Everything else is automated.

## 결정
- `.github/workflows/release.yml`: 태그 `vX.Y.Z`를 푸시하면 테스트를 돌리고, 태그와 `pyproject.toml` 버전이 같은지 확인한 뒤 빌드·검사·업로드한다. 토큰은 시크릿 `PYPI_API_TOKEN`을 쓴다.
- 첫 배포는 0.1.0(알파)이다. 이것으로 `pickaxetax` 이름을 확보한다.
- 패키지 메타데이터는 SPDX 라이선스 표기, 프로젝트 링크, 분류 태그를 갖춘다. README 링크는 PyPI 페이지에서도 동작하도록 절대경로로 쓴다.
- Pages는 저장소 기본 브랜치에 `site/` 변경이 푸시될 때 배포한다. 수동 실행도 가능하다.

## 실행 기록
- 2026-10-05: 0.1.0을 PyPI에 배포했다. https://pypi.org/project/pickaxetax/ 공개 인덱스에서 `pip install pickaxetax==0.1.0`과 `pxt --help` 동작을 확인했다.
- 같은 날 GitHub Pages 배포가 성공했다. https://graviton94.github.io/pickaxetax/
- 작업 세션의 git 권한은 작업 브랜치 푸시로 한정되어 있어 태그 푸시가 거부되었다. 그래서 release 워크플로를 수동 실행(workflow_dispatch)해 배포했다. 이후 릴리스도 `pyproject.toml` 버전을 올리고 release 워크플로를 실행하면 된다. 태그 푸시 방식도 그대로 지원한다.

## 운영 분담
대표의 지시에 따라 **대표는 본인 인증이 필요한 일**(계정 가입, 토큰 발급, 시크릿 입력)만 맡는다. 나머지(빌드, 배포, 태그, 문서, 검증)는 모두 자동화하거나 작업자가 처리한다.

## 후속 권고 (보안)
- 첫 업로드 뒤에는 계정 전체 범위의 토큰을 pickaxetax 프로젝트 전용 토큰으로 교체하거나 Trusted Publishing(OIDC)으로 전환한다.
