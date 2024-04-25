FROM public.int.repositories.cloud.sap/com.sap.datahub.linuxx86_64/hanalite-build:0.0.15

COPY infrabox_key \
     infrabox_key.pub \
     known_hosts \
     /root/.ssh/

ADD clone.sh e2e/clone.sh
RUN /e2e/clone.sh

CMD "/vora/scripts/elvis.py"
