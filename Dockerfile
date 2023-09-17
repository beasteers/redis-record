FROM python:3.10-slim
# # opencv is installed then uninstalled apparently because it gives us some dependencies that we need
# # then we reinstall opencv using pip. Idk ask the original authors
# RUN apt-get update -qyy && \
#     apt-get install -y  python3-opencv && apt-get remove -y python3-opencv \
#     && pip install --upgrade pip \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# install
ADD setup.py .
ADD ./redis_record/__init__.py redis_record/__init__.py
RUN pip install -e .
ADD ./redis_record /src/redis_record

ENTRYPOINT [ "python" ]
CMD [ "-m", "redis_record.record"]