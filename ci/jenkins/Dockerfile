# Jenkins for Miko: the official Jenkins image plus conda (Miniforge).
# Miniforge is conda with conda-forge as its default channel, so the commands are the
# same as Miniconda on my laptop. Python 3.11 and Java 17 for the tests come from
# environment.yml, exactly like on the laptop.
FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/miniforge.sh \
      https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh \
 && bash /tmp/miniforge.sh -b -p /opt/conda \
 && rm /tmp/miniforge.sh \
 && chown -R jenkins:jenkins /opt/conda
ENV PATH="/opt/conda/bin:${PATH}"

USER jenkins
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
